"""
Execution nodes for Catalog & Product Agent sub-graph.
"""

import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Any, Dict, List
from google import genai

from app.core.config import settings
from app.schemas.knowledge import SearchRequest, SearchFilter
from app.services.search import search_service
from app.agents.catalog.state import CatalogAgentState
from app.agents.catalog.prompts import (
    CATALOG_FALLBACK_REPLY,
    build_catalog_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent cho tư vấn sản phẩm, tìm kiếm, giá
# ---------------------------------------------------------------------------
def analyze_catalog_query_node(state: CatalogAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection cho tìm đồ, hỏi giá sản phẩm, thanh lý và so sánh thuê/mua.
    """
    msg = state["message"].lower()
    sub_intent = "general"

    if any(kw in msg for kw in ["nên thuê hay mua", "thuê hay thanh lý", "dùng 1 lần thì nên", "tư vấn thuê hay mua"]):
        sub_intent = "rent_vs_liquidation"
    elif any(kw in msg for kw in ["thanh lý", "tly", "thanh ly", "đồ cũ", "pass đồ", "mua thanh lý"]):
        sub_intent = "liquidation_items"
    elif any(kw in msg for kw in ["giá bao nhiêu", "nhiêu tiền", "giá thuê cái này", "báo giá váy", "chi phí thuê"]):
        sub_intent = "product_price"
    elif any(kw in msg for kw in ["tìm", "có mẫu", "mẫu nào", "váy", "đầm", "áo dài", "đi tiệc", "dạ hội", "size", "màu"]):
        sub_intent = "product_search"

    logger.info("  └── [CatalogAgent:SubIntent] Sub-intent detected: '%s' (message='%s')", sub_intent, state["message"])
    return {"sub_intent": sub_intent}


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search theo topic sản phẩm & thanh lý
# ---------------------------------------------------------------------------
SUB_INTENT_TO_TOPIC = {
    "product_search":      "product_search",
    "product_price":       "product_price",
    "rent_vs_liquidation": "rent_or_liquidation",
    "liquidation_items":   "liquidation",
    "general":             "product_search",
}


def retrieve_catalog_knowledge_node(state: CatalogAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic phù hợp, top_k=3.
    Nếu không có kết quả sẽ fallback sang free search.
    """
    sub_intent = state.get("sub_intent", "general")
    topic = SUB_INTENT_TO_TOPIC.get(sub_intent, "product_search")

    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(status="active", topic=topic),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0:
        logger.warning("  └── [CatalogAgent:Knowledge] Khong tim thay topic=%s, fallback free search.", topic)
        search_req.filter.topic = None
        search_res = search_service.search_knowledge(search_req)

    chunks: List[str] = []
    sources: List[Dict[str, Any]] = []

    for item in search_res.results:
        chunks.append(f"- {item.content}")
        sources.append({
            "chunk_id": item.chunk_id,
            "document_id": item.metadata.document_id,
            "record_id": item.metadata.record_id,
            "score": item.score,
            "source_url": item.metadata.source_url,
        })

    logger.info("  └── [CatalogAgent:Knowledge] Qdrant: %d chunks retrieved (filter=%s)", len(chunks), topic)
    return {"retrieved_chunks": chunks, "sources": sources}


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với prompt chuyên biệt Stylist & Catalog
# ---------------------------------------------------------------------------
def generate_catalog_response_node(state: CatalogAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini với prompt chuyên biệt của Catalog Agent.
    """
    context_str = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "Rentzy sở hữu bộ sưu tập đa dạng các mẫu đầm dạ hội, váy tiệc thiết kế và trang phục cưới cao cấp."
    )

    prompt = build_catalog_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "general"),
    )

    logger.info("  └── [CatalogAgent:LLM] Generating response via Gemini (model=%s)...", settings.LLM_MODEL_NAME)
    from app.services.llm import llm_service
    try:
        res = llm_service.generate_content(contents=prompt)
        reply = res.text.strip()
    except Exception as exc:
        logger.error("  └── [CatalogAgent:LLM] Loi Gemini generate: %s", exc)
        reply = CATALOG_FALLBACK_REPLY

    logger.info(
        "  └── [CatalogAgent:Done] Response ready (%d chars, sub_intent='%s')",
        len(reply),
        state.get("sub_intent", "general"),
    )

    return {
        "reply_message": reply,
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "catalog_agent",
    }
