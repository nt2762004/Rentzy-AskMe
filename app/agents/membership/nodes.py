"""
Execution nodes for Membership Agent sub-graph.
"""

import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Any, Dict, List

from google import genai

from app.core.config import settings
from app.schemas.knowledge import SearchRequest, SearchFilter
from app.services.search import search_service
from app.agents.membership.state import MembershipAgentState
from app.agents.membership.prompts import (
    MEMBERSHIP_REGISTER_URL,
    MEMBERSHIP_FALLBACK_REPLY,
    build_membership_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent
# ---------------------------------------------------------------------------
def analyze_membership_query_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection. Fallback sang 'overview' nếu không rõ.
    """
    msg = state["message"].lower()
    sub_intent = "overview"

    if any(kw in msg for kw in ["dang ky", "đăng ký", "tham gia", "mua gói", "muốn có", "sign up"]):
        sub_intent = "register"
    elif any(kw in msg for kw in ["so sánh", "khác nhau", "phân biệt", "nên chọn"]):
        sub_intent = "compare"
    elif any(kw in msg for kw in ["giá", "phí", "bao nhiêu tiền", "chi phí", "bao nhiêu"]):
        sub_intent = "pricing"
    elif any(kw in msg for kw in ["quyền lợi", "ưu đãi", "được gì", "bao gồm", "lợi ích"]):
        sub_intent = "benefits"
    elif any(kw in msg for kw in ["gia hạn", "nâng cấp", "renew", "upgrade"]):
        sub_intent = "renew"

    logger.info("  └── [MembershipAgent:SubIntent] Sub-intent detected: '%s' (message='%s')", sub_intent, state["message"])
    return {"sub_intent": sub_intent}


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search với topic=membership
# ---------------------------------------------------------------------------
def retrieve_membership_knowledge_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic=membership, top_k=5.
    Nếu không có kết quả sẽ fallback sang free search.
    """
    search_req = SearchRequest(
        query=state["message"],
        top_k=5,
        filter=SearchFilter(status="active", topic="membership"),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0:
        logger.warning("  └── [MembershipAgent:Knowledge] Khong tim thay topic=membership, fallback free search.")
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

    logger.info("  └── [MembershipAgent:Knowledge] Qdrant: %d chunks retrieved (filter=membership)", len(chunks))
    return {"retrieved_chunks": chunks, "sources": sources}


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với prompt chuyên biệt Membership
# ---------------------------------------------------------------------------
def generate_membership_response_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini với prompt chuyên biệt cho Membership.
    Luôn đảm bảo có link https://rentzy.vn/member-ship/ trong reply.
    """
    context_str = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "Chưa tìm thấy thông tin chi tiết về gói thành viên trong hệ thống."
    )

    prompt = build_membership_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "overview"),
    )

    logger.info("  └── [MembershipAgent:LLM] Generating response via Gemini (model=%s)...", settings.LLM_MODEL_NAME)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        res = client.models.generate_content(model=settings.LLM_MODEL_NAME, contents=prompt)
        reply = res.text.strip()
    except Exception as exc:
        logger.error("  └── [MembershipAgent:LLM] Loi Gemini generate: %s", exc)
        reply = MEMBERSHIP_FALLBACK_REPLY

    # Đảm bảo link luôn xuất hiện
    if MEMBERSHIP_REGISTER_URL not in reply:
        reply += f"\n\n{MEMBERSHIP_REGISTER_URL}"

    logger.info(
        "  └── [MembershipAgent:Done] Response ready (%d chars, sub_intent='%s', link_verified=True)",
        len(reply),
        state.get("sub_intent", "overview"),
    )

    return {
        "reply_message": reply,
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "membership_agent",
    }
