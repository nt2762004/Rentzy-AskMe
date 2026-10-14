"""
Execution nodes for Membership Agent sub-graph with Agentic Tool Calling.
"""

import logging
import warnings
warnings.filterwarnings("ignore")

import re
from typing import Any, Dict, List

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.greetings import strip_opening_greeting
from app.schemas.knowledge import SearchRequest, SearchFilter
from app.services.search import search_service
from app.services.web_reader import web_reader_service
from app.agents.membership.state import MembershipAgentState
from app.agents.membership.tools import fetch_web_page
from app.agents.membership.prompts import (
    MEMBERSHIP_REGISTER_URL,
    MEMBERSHIP_FALLBACK_REPLY,
    build_membership_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Node 1: Analyze Query — nhận diện sub-intent (hỗ trợ web_lookup)
# ---------------------------------------------------------------------------
def analyze_membership_query_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Rule-based sub-intent detection. Fallback sang 'overview' nếu không rõ.
    """
    msg = state["message"].lower()
    sub_intent = "overview"

    # Kiểm tra URL hoặc nhu cầu tra cứu link/web
    urls = web_reader_service.extract_urls(state["message"])
    if urls or any(kw in msg for kw in ["tra cứu", "link", "url", "website", "trên web", "trên mạng", "trang web", "web"]):
        sub_intent = "web_lookup"
    elif any(kw in msg for kw in ["dang ky", "đăng ký", "tham gia", "mua gói", "muốn có", "sign up"]):
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


def _clean_support_from_chunk(text: str) -> str:
    """Loại bỏ câu chứa hotline hoặc showroom trong chunk tri thức để không làm nhiễu LLM."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if any(kw in line.lower() for kw in ["0798969040", "51 đường số 41"]):
            cleaned_line = re.sub(r"(?:Nếu Nàng cần|Nàng có thể|Vui lòng)[^.\n]*(?:hotline|0798969040|showroom|51 đường số 41)[^.\n]*(?:\.|$)", "", line)
            if cleaned_line.strip():
                cleaned.append(cleaned_line.strip())
        else:
            cleaned.append(line)
    return "\n".join(cleaned)


def _strip_unsolicited_contact_info(text: str) -> str:
    """Loại bỏ dòng tự ý đưa hotline hoặc địa chỉ showroom khi người dùng không yêu cầu."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line_clean = line.strip()
        if any(kw in line_clean.lower() for kw in ["0798969040", "51 đường số 41"]) or (
            any(kw in line_clean.lower() for kw in ["hotline", "showroom", "ghé showroom", "liên hệ hotline"])
            and not any(pkg in line_clean for pkg in ["DC2990", "DC3990", "DC6990", "DC9990"])
        ):
            continue
        cleaned_lines.append(line)
    res = "\n".join(cleaned_lines)
    return re.sub(r"\n{3,}", "\n\n", res).strip()


# ---------------------------------------------------------------------------
# Node 2: Retrieve Knowledge — Qdrant search + Web Lookup Dual Guarantee
# ---------------------------------------------------------------------------
def retrieve_membership_knowledge_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Truy xuất knowledge từ Qdrant với filter topic=membership, top_k=5.
    Nếu phát hiện URL hoặc sub_intent=web_lookup, cào dữ liệu web trực tiếp
    vào chunks làm context dự phòng (Dual-Guarantee).
    """
    chunks: List[str] = []
    sources: List[Dict[str, Any]] = []

    # 1. Kiểm tra URL trong tin nhắn hoặc sub_intent web_lookup để cào dữ liệu web
    urls = web_reader_service.extract_urls(state["message"])
    if urls:
        for idx, url in enumerate(urls):
            logger.info("  └── [MembershipAgent:Knowledge] Phát hiện URL '%s' trong câu hỏi, đang nạp dữ liệu...", url)
            web_content = web_reader_service.fetch_url(url)
            chunks.append(f"[Nội dung tra cứu từ link {url}]:\n{web_content}")
            sources.append({
                "chunk_id": f"web_{idx}_{abs(hash(url))}",
                "document_id": "web_live",
                "record_id": "web_live",
                "score": 1.0,
                "source_url": url,
            })
    elif state.get("sub_intent") == "web_lookup":
        # Không có URL cụ thể -> pre-fetch trang membership chính thức
        default_url = MEMBERSHIP_REGISTER_URL
        logger.info("  └── [MembershipAgent:Knowledge] Sub-intent là web_lookup, nạp trước URL chính thức: %s", default_url)
        web_content = web_reader_service.fetch_url(default_url)
        chunks.append(f"[Nội dung trang chính thức {default_url}]:\n{web_content}")
        sources.append({
            "chunk_id": f"web_default_{abs(hash(default_url))}",
            "document_id": "web_live",
            "record_id": "web_live",
            "score": 1.0,
            "source_url": default_url,
        })

    # 2. Truy xuất thêm từ Vector DB Qdrant
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

    for item in search_res.results:
        cleaned_chunk = _clean_support_from_chunk(item.content)
        chunks.append(f"- {cleaned_chunk}")
        sources.append({
            "chunk_id": item.chunk_id,
            "document_id": item.metadata.document_id,
            "record_id": item.metadata.record_id,
            "score": item.score,
            "source_url": item.metadata.source_url,
        })

    logger.info("  └── [MembershipAgent:Knowledge] Total chunks: %d (web=%d, qdrant=%d)", len(chunks), 1 if (urls or state.get("sub_intent") == "web_lookup") else 0, len(search_res.results))
    return {"retrieved_chunks": chunks, "sources": sources}


# ---------------------------------------------------------------------------
# Node 3: Generate Response — Gemini với Tool Calling fetch_web_page
# ---------------------------------------------------------------------------
def generate_membership_response_node(state: MembershipAgentState) -> Dict[str, Any]:
    """
    Sinh câu trả lời bằng Gemini tích hợp Agentic Tool Calling (fetch_web_page).
    Luôn đảm bảo có link https://rentzy.vn/member-ship/ trong reply.
    """
    context_str = (
        "\n\n".join(state["retrieved_chunks"])
        if state.get("retrieved_chunks")
        else "Chưa tìm thấy thông tin chi tiết về gói thành viên trong hệ thống."
    )

    is_first_turn = state.get("is_first_turn", True)
    prompt = build_membership_prompt(
        context_str=context_str,
        message=state["message"],
        sub_intent=state.get("sub_intent", "overview"),
        is_first_turn=is_first_turn,
    )

    logger.info("  └── [MembershipAgent:LLM] Generating response via Gemini Tool-Calling (model=%s, tool=fetch_web_page)...", settings.LLM_MODEL_NAME)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    reply = ""

    # Kích hoạt Agentic Tool Calling thông qua Gemini Chat AFC
    try:
        chat = client.chats.create(
            model=settings.LLM_MODEL_NAME,
            config=types.GenerateContentConfig(
                tools=[fetch_web_page],
                temperature=0.2,
            ),
        )
        res = chat.send_message(prompt)
        if res and res.text:
            reply = res.text.strip()
    except Exception as exc:
        logger.warning("  └── [MembershipAgent:LLM] Tool-calling chat gap loi (%s), fallback sang generate_content...", exc)
        try:
            res = client.models.generate_content(model=settings.LLM_MODEL_NAME, contents=prompt)
            if res and res.text:
                reply = res.text.strip()
        except Exception as exc_gen:
            logger.error("  └── [MembershipAgent:LLM] Loi Gemini generate_content: %s", exc_gen)
            reply = MEMBERSHIP_FALLBACK_REPLY

    if not reply:
        reply = MEMBERSHIP_FALLBACK_REPLY

    # Loại bỏ câu chào lặp lại nếu không phải lượt đầu tiên trong phiên
    if not is_first_turn:
        reply = strip_opening_greeting(reply)

    # Loại bỏ thông tin hotline / showroom nếu khách không yêu cầu
    msg_lower = state["message"].lower()
    if not any(kw in msg_lower for kw in ["hotline", "số điện thoại", "sđt", "địa chỉ", "showroom", "ở đâu"]):
        reply = _strip_unsolicited_contact_info(reply)

    # Đảm bảo link đăng ký luôn xuất hiện ở cuối
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

