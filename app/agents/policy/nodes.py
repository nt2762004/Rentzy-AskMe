"""
Execution nodes for Policy Agent sub-graph.
"""

import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Any, Dict, List
from google import genai

from app.core.config import settings
from app.schemas.knowledge import SearchRequest, SearchFilter
from app.services.search import search_service
from app.services.llm import llm_service
from app.agents.policy.state import PolicyAgentState
from app.agents.policy.prompts import (
    POLICY_FALLBACK_REPLY,
    build_policy_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent cho các chính sách thuê đồ
# ---------------------------------------------------------------------------
def analyze_policy_query_node(state: PolicyAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection cho các câu hỏi chính sách cọc, hoàn cọc, giao nhận, giá thuê.
    """
    msg = state["message"].lower()
    sub_intent = "general"

    if any(refund_kw in msg for refund_kw in ["hoàn", "trả lại", "lấy lại", "nhận lại", "thời gian hoàn"]) and "cọc" in msg:
        sub_intent = "deposit_refund"
    elif any(kw in msg for kw in ["đặt cọc", "cọc bao nhiêu", "tiền cọc", "cọc cccd", "phí cọc", "hủy cọc", "đổi mẫu", "hình thức cọc", "cọc"]):
        sub_intent = "deposit_rules"
    elif any(kw in msg for kw in ["giá thuê", "bảng giá", "thời gian thuê", "mấy ngày", "trễ hạn", "phụ phí", "tính giá"]):
        sub_intent = "rental_pricing"
    elif any(kw in msg for kw in ["giao hàng", "nhận đồ", "trả đồ", "shipper", "giặt", "giặt ủi", "thử khi nhận"]):
        sub_intent = "receive_and_return"

    logger.info("  └── [PolicyAgent:SubIntent] Sub-intent detected: '%s' (message='%s')", sub_intent, state["message"])
    return {"sub_intent": sub_intent}


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search theo topic nghiệp vụ
# ---------------------------------------------------------------------------
SUB_INTENT_TO_TOPIC = {
    "deposit_refund":     "deposit_refund",
    "deposit_rules":      "deposit_policy",
    "rental_pricing":     "rental_pricing",
    "receive_and_return": "receive_return",
    "general":            "deposit_policy",
}


def retrieve_policy_knowledge_node(state: PolicyAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic phù hợp, top_k=3.
    Nếu không có kết quả sẽ fallback sang free search.
    """
    sub_intent = state.get("sub_intent", "general")
    topic = SUB_INTENT_TO_TOPIC.get(sub_intent, "deposit_policy")

    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(status="active", topic=topic),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0:
        logger.warning("  └── [PolicyAgent:Knowledge] Khong tim thay topic=%s, fallback free search.", topic)
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

    logger.info("  └── [PolicyAgent:Knowledge] Qdrant: %d chunks retrieved (filter=%s)", len(chunks), topic)
    return {"retrieved_chunks": chunks, "sources": sources}


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với prompt chuyên biệt Policy
# ---------------------------------------------------------------------------
def generate_policy_response_node(state: PolicyAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini với prompt chuyên biệt của Policy Agent.
    """
    context_str = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "Rentzy quy định đặt cọc bằng CCCD hoặc tiền mặt. Hoàn cọc trong vòng 24h sau khi kiểm tra trả đồ."
    )

    prompt = build_policy_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "general"),
    )

    logger.info("  └── [PolicyAgent:LLM] Generating response via Gemini (model pool: %s)...", llm_service.get_model_pool())
    try:
        res = llm_service.generate_content(contents=prompt)
        reply = res.text.strip()
    except Exception as exc:
        logger.error("  └── [PolicyAgent:LLM] Loi Gemini generate: %s", exc)
        reply = POLICY_FALLBACK_REPLY

    logger.info(
        "  └── [PolicyAgent:Done] Response ready (%d chars, sub_intent='%s')",
        len(reply),
        state.get("sub_intent", "general"),
    )

    return {
        "reply_message": reply,
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "policy_agent",
    }
