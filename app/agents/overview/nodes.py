"""
Execution nodes for Overview Agent sub-graph.
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
from app.agents.overview.state import OverviewAgentState
from app.agents.overview.prompts import (
    OVERVIEW_FALLBACK_REPLY,
    build_overview_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent cho câu hỏi tổng quan
# ---------------------------------------------------------------------------
def analyze_overview_query_node(state: OverviewAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection cho các câu hỏi tổng quan / thương hiệu Rentzy.
    """
    msg = state["message"].lower()
    sub_intent = "general"

    if any(kw in msg for kw in ["ở đâu", "showroom", "địa chỉ", "cửa hàng ở đâu", "shop ở đâu", "đến đâu", "thử đồ"]):
        sub_intent = "showroom_address"
    elif any(kw in msg for kw in ["hotline", "số điện thoại", "sđt", "liên hệ", "gọi cho"]):
        sub_intent = "hotline_contact"
    elif any(kw in msg for kw in ["mô hình", "tại sao nên thuê", "thuê là sao", "tủ đồ", "hoạt động thế nào"]):
        sub_intent = "business_model"
    elif any(kw in msg for kw in ["rentzy là gì", "giới thiệu", "rentzy là ai", "rentzy là"]):
        sub_intent = "brand_intro"

    logger.info("  └── [OverviewAgent:SubIntent] Sub-intent detected: '%s' (message='%s')", sub_intent, state["message"])
    return {"sub_intent": sub_intent}


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search với topic=rentzy_overview
# ---------------------------------------------------------------------------
def retrieve_overview_knowledge_node(state: OverviewAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic=rentzy_overview, top_k=3.
    Nếu không có kết quả sẽ fallback sang free search.
    """
    topic = "showroom_fitting" if any(w in state["message"].lower() for w in ["thử", "fitting", "mặc thử"]) else "rentzy_overview"
    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(status="active", topic=topic),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0:
        logger.warning("  └── [OverviewAgent:Knowledge] Khong tim thay topic=%s, fallback free search.", topic)
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

    logger.info("  └── [OverviewAgent:Knowledge] Qdrant: %d chunks retrieved (filter=rentzy_overview)", len(chunks))
    return {"retrieved_chunks": chunks, "sources": sources}


import re


def _strip_unsolicited_contact_info(text: str) -> str:
    """Loại bỏ dòng tự ý đưa hotline hoặc địa chỉ showroom khi người dùng không yêu cầu."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line_clean = line.strip()
        if any(kw in line_clean.lower() for kw in ["0798969040", "51 đường số 41"]) or (
            any(kw in line_clean.lower() for kw in ["hotline", "showroom", "ghé showroom", "liên hệ hotline"])
        ):
            continue
        cleaned_lines.append(line)
    res = "\n".join(cleaned_lines)
    return re.sub(r"\n{3,}", "\n\n", res).strip()


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với prompt chuyên biệt Overview
# ---------------------------------------------------------------------------
def generate_overview_response_node(state: OverviewAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini với prompt chuyên biệt của Overview Agent.
    """
    context_str = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "Rentzy là dịch vụ cho thuê trang phục dạ hội và thời trang cao cấp tại TP. Hồ Chí Minh."
    )

    is_first_turn = state.get("is_first_turn", True)
    prompt = build_overview_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "general"),
        is_first_turn=is_first_turn,
    )

    logger.info("  └── [OverviewAgent:LLM] Generating response via Gemini (model=%s)...", settings.LLM_MODEL_NAME)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        res = client.models.generate_content(model=settings.LLM_MODEL_NAME, contents=prompt)
        reply = res.text.strip()
    except Exception as exc:
        logger.error("  └── [OverviewAgent:LLM] Loi Gemini generate: %s", exc)
        reply = OVERVIEW_FALLBACK_REPLY

    # Loại bỏ câu chào lặp lại nếu không phải lượt đầu tiên trong phiên
    if not is_first_turn:
        reply = strip_opening_greeting(reply)

    # Chỉ đưa Hotline / Showroom nếu người dùng có yêu cầu hoặc sub_intent yêu cầu
    sub_intent = state.get("sub_intent", "general")
    msg_lower = state["message"].lower()
    has_contact_req = any(kw in msg_lower for kw in ["ở đâu", "địa chỉ", "showroom", "cửa hàng ở đâu", "shop ở đâu", "thử đồ", "hotline", "số điện thoại", "sđt", "liên hệ", "gọi"])
    if sub_intent not in ("showroom_address", "hotline_contact") and not has_contact_req:
        reply = _strip_unsolicited_contact_info(reply)

    logger.info(
        "  └── [OverviewAgent:Done] Response ready (%d chars, sub_intent='%s')",
        len(reply),
        state.get("sub_intent", "general"),
    )

    return {
        "reply_message": reply,
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": "overview_agent",
    }
