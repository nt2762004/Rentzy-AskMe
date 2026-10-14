"""
Execution nodes for Support Agent sub-graph.
"""

import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Any, Dict, List
from google import genai

from app.core.config import settings
from app.core.greetings import strip_opening_greeting
from app.schemas.knowledge import SearchRequest, SearchFilter
from app.services.search import search_service
from app.agents.support.state import SupportAgentState
from app.agents.support.prompts import (
    SUPPORT_FALLBACK_REPLY,
    build_support_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent cho liên hệ & hỗ trợ CSKH
# ---------------------------------------------------------------------------
def analyze_support_query_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection cho các câu hỏi CSKH, Hotline, gặp tư vấn viên.
    """
    msg = state["message"].lower()
    sub_intent = "general"

    if any(kw in msg for kw in ["đơn hàng", "mã đơn", "tra cứu đơn", "tình trạng đơn", "chưa nhận được đồ", "hủy đơn"]):
        sub_intent = "order_support"
    elif any(kw in msg for kw in ["khiếu nại", "rách", "hư hỏng", "lỗi đồ", "sự cố", "đổi gấp"]):
        sub_intent = "complaint"
    elif any(kw in msg for kw in ["gặp nhân viên", "tư vấn viên", "người thật", "chuyên viên", "chat trực tiếp", "nói chuyện với người"]):
        sub_intent = "human_agent"
    elif any(kw in msg for kw in ["hotline", "số điện thoại", "sđt", "gọi điện", "liên hệ hotline"]):
        sub_intent = "hotline_call"

    logger.info("  └── [SupportAgent:SubIntent] Sub-intent detected: '%s' (message='%s')", sub_intent, state["message"])
    return {"sub_intent": sub_intent}


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search với topic=contact_support / order_support
# ---------------------------------------------------------------------------
def retrieve_support_knowledge_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic=contact_support hoặc order_support, top_k=3.
    Nếu không có kết quả sẽ fallback sang free search.
    """
    topic = "order_support" if state.get("sub_intent") == "order_support" else "contact_support"

    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(status="active", topic=topic),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0:
        logger.warning("  └── [SupportAgent:Knowledge] Khong tim thay topic=%s, fallback free search.", topic)
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

    logger.info("  └── [SupportAgent:Knowledge] Qdrant: %d chunks retrieved (filter=%s)", len(chunks), topic)
    return {"retrieved_chunks": chunks, "sources": sources}


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với prompt chuyên biệt Support
# ---------------------------------------------------------------------------
def generate_support_response_node(state: SupportAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini với prompt chuyên biệt của Support Agent.
    """
    context_str = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "Rentzy hỗ trợ khách hàng qua Hotline 0798969040 và Showroom tại 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh."
    )

    is_first_turn = state.get("is_first_turn", True)
    prompt = build_support_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "general"),
        is_first_turn=is_first_turn,
    )

    logger.info("  └── [SupportAgent:LLM] Generating response via Gemini (model=%s)...", settings.LLM_MODEL_NAME)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        res = client.models.generate_content(model=settings.LLM_MODEL_NAME, contents=prompt)
        reply = res.text.strip()
    except Exception as exc:
        logger.error("  └── [SupportAgent:LLM] Loi Gemini generate: %s", exc)
        reply = SUPPORT_FALLBACK_REPLY

    # Loại bỏ câu chào lặp lại nếu không phải lượt đầu tiên trong phiên
    if not is_first_turn:
        reply = strip_opening_greeting(reply)

    logger.info(
        "  └── [SupportAgent:Done] Response ready (%d chars, sub_intent='%s')",
        len(reply),
        state.get("sub_intent", "general"),
    )

    return {
        "reply_message": reply,
        "suggest_sales": True,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "support_agent",
    }
