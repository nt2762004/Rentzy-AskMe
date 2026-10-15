import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.intents import INTENT_CATALOG, IntentEnum, INTENT_TO_TOPIC_MAP
from app.core.greetings import (
    is_simple_greeting,
    strip_opening_greeting,
    FAST_REPLY_GREETING_MESSAGE,
    FAST_REPLY_CONTINUATION_GREETING_MESSAGE,
    FAST_REPLY_SUGGESTED_OPTIONS,
)
from app.services.classifier import intent_classifier
from app.services.session import session_service
from app.services.search import search_service
from app.schemas.knowledge import SearchRequest, SearchFilter

# Sub-agents
from app.agents import membership, overview, support, policy, catalog

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AgentState — shared state across all nodes
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    session_id: str
    message: str
    chat_history: List[Dict[str, str]]
    intent: str
    intent_title: str
    confidence: float
    need_clarification: bool
    suggest_sales: bool
    suggested_options: Optional[List[str]]
    reply_message: str
    fallback_count: int
    sources: Optional[List[Dict[str, Any]]]
    handled_by: Optional[str]
    is_first_turn: Optional[bool]
    is_greeting: Optional[bool]


# ---------------------------------------------------------------------------
# Node 0: Preprocess Input (Check Greeting & First Turn)
# ---------------------------------------------------------------------------
def preprocess_input_node(state: AgentState) -> Dict[str, Any]:
    """
    Tiền xử lý tin nhắn:
    - Đọc chat history từ session store
    - Xác định lượt đầu tiên (is_first_turn): True nếu chưa có câu trả lời nào của assistant trong session
    - Kiểm tra xem có phải câu chào hỏi đơn giản (is_greeting) để áp dụng Fast Reply không cần gọi LLM
    """
    session = session_service.get_session(state["session_id"])
    chat_history_dicts = [m.model_dump() for m in session.messages]
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]
    is_first_turn = len(assistant_msgs) == 0
    is_greeting = is_simple_greeting(state["message"])

    logger.info(
        "\n============================================================\n"
        "[Supervisor:Inbound] Session=%s | Message='%s' | FirstTurn=%s | FastGreeting=%s",
        state["session_id"],
        state["message"],
        is_first_turn,
        is_greeting,
    )

    return {
        "chat_history": chat_history_dicts,
        "is_first_turn": is_first_turn,
        "is_greeting": is_greeting,
    }


# ---------------------------------------------------------------------------
# Node 0b: Fast Reply Greeting (Zero LLM / Instant response < 5ms)
# ---------------------------------------------------------------------------
def fast_reply_greeting_node(state: AgentState) -> Dict[str, Any]:
    """
    Cơ chế phản hồi nhanh trực tiếp cho các câu chào đơn giản (hello, xin chào, alo...)
    mà KHÔNG cần gọi LLM (Gemini Classifier hay Agent), tối ưu độ trễ và tiết kiệm quota.
    """
    session_service.reset_fallback_count(state["session_id"])
    is_first = state.get("is_first_turn", True)
    reply = FAST_REPLY_GREETING_MESSAGE if is_first else FAST_REPLY_CONTINUATION_GREETING_MESSAGE

    logger.info("[Supervisor:FastReply] Phản hồi trực tiếp câu chào (FirstTurn=%s, Zero LLM)", is_first)

    return {
        "intent": IntentEnum.RENTZY_OVERVIEW.value,
        "intent_title": "Chào hỏi & Giới thiệu",
        "confidence": 1.0,
        "need_clarification": False,
        "suggest_sales": False,
        "suggested_options": FAST_REPLY_SUGGESTED_OPTIONS,
        "reply_message": reply,
        "fallback_count": 0,
        "sources": [],
        "handled_by": "fast_reply_greeting",
    }


# ---------------------------------------------------------------------------
# Node 1: Classify Intent
# ---------------------------------------------------------------------------
def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Phân loại ý định của tin nhắn người dùng."""
    session = session_service.get_session(state["session_id"])
    chat_history_dicts = state.get("chat_history") or [m.model_dump() for m in session.messages]

    result = intent_classifier.classify(state["message"], chat_history=chat_history_dicts)
    intent_info = INTENT_CATALOG.get(result.intent, {})
    intent_title = intent_info.get("title", "Không xác định")

    logger.info(
        "[Supervisor:Classifier] Intent: %s ('%s') | Confidence: %.2f | Clarification: %s",
        result.intent,
        intent_title,
        result.confidence,
        result.need_clarification,
    )

    session.current_intent = result.intent
    session_service.save_session(session)

    return {
        "intent": result.intent,
        "intent_title": intent_title,
        "confidence": result.confidence,
        "need_clarification": result.need_clarification,
        "suggested_options": result.suggested_options,
        "fallback_count": session.fallback_count,
    }


# ---------------------------------------------------------------------------
# Node 2a: Membership Agent Node  (delegates to sub-graph)
# ---------------------------------------------------------------------------
def membership_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Uỷ quyền hoàn toàn cho Membership Agent (sub-graph riêng).
    """
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Delegate] Chuyen giao sang [MembershipAgent]")
    output = membership.run(state)
    output["handled_by"] = "membership_agent"
    return output


# ---------------------------------------------------------------------------
# Node 2b: Overview Agent Node  (delegates to sub-graph)
# ---------------------------------------------------------------------------
def overview_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Uỷ quyền hoàn toàn cho Overview Agent (sub-graph riêng).
    """
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Delegate] Chuyen giao sang [OverviewAgent]")
    output = overview.run(state)
    output["handled_by"] = "overview_agent"
    return output


# ---------------------------------------------------------------------------
# Node 2c: Support Agent Node (delegates to sub-graph)
# ---------------------------------------------------------------------------
def support_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Uỷ quyền hoàn toàn cho Support Agent (sub-graph riêng).
    """
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Delegate] Chuyen giao sang [SupportAgent]")
    output = support.run(state)
    output["handled_by"] = "support_agent"
    return output


# ---------------------------------------------------------------------------
# Node 2d: Policy Agent Node (delegates to sub-graph)
# ---------------------------------------------------------------------------
def policy_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Uỷ quyền hoàn toàn cho Policy Agent (sub-graph riêng).
    """
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Delegate] Chuyen giao sang [PolicyAgent]")
    output = policy.run(state)
    output["handled_by"] = "policy_agent"
    return output


# ---------------------------------------------------------------------------
# Node 2e: Catalog Agent Node (delegates to sub-graph)
# ---------------------------------------------------------------------------
def catalog_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Uỷ quyền hoàn toàn cho Catalog Agent (sub-graph riêng).
    """
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Delegate] Chuyen giao sang [CatalogAgent]")
    output = catalog.run(state)
    output["handled_by"] = "catalog_agent"
    return output





# ---------------------------------------------------------------------------
# Node 2b: Retrieve Knowledge (generic — cho các intent active khác)
# ---------------------------------------------------------------------------
def retrieve_knowledge_node(state: AgentState) -> Dict[str, Any]:
    """Lấy tri thức từ Qdrant và tổng hợp câu trả lời bằng Gemini."""
    session_service.reset_fallback_count(state["session_id"])

    topic_filter = INTENT_TO_TOPIC_MAP.get(state["intent"], state["intent"])
    if topic_filter == "fallback":
        topic_filter = None

    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(status="active", topic=topic_filter),
    )
    search_res = search_service.search_knowledge(search_req)

    if search_res.total_results == 0 and topic_filter:
        search_req.filter.topic = None
        search_res = search_service.search_knowledge(search_req)

    context_texts: List[str] = []
    sources: List[Dict[str, Any]] = []
    for item in search_res.results:
        context_texts.append(f"- {item.content}")
        sources.append({
            "chunk_id": item.chunk_id,
            "document_id": item.metadata.document_id,
            "record_id": item.metadata.record_id,
            "score": item.score,
            "source_url": item.metadata.source_url,
        })

    context_str = "\n".join(context_texts) if context_texts else "Chưa tìm thấy bài viết chi tiết trong hệ thống."

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    is_first_turn = state.get("is_first_turn", True)
    greeting_instruction = (
        "- Đây là lượt trao đổi TIẾP THEO trong phiên hội thoại. TUYỆT ĐỐI KHÔNG mở đầu bằng câu chào hỏi (như 'Chào Nàng,', 'Dạ chào Nàng,', 'Rentzy xin chào Nàng,'). Hãy trả lời trực tiếp vào nội dung câu hỏi."
        if not is_first_turn
        else "- Nếu mở đầu bằng lời chào, chỉ chào ngắn gọn 1 lần ở đầu câu (ví dụ 'Chào Nàng,')."
    )

    prompt = (
        "Bạn là Trợ lý AI AskMe của thương hiệu thời trang Rentzy.\n"
        "Dựa vào ngữ cảnh thông tin chính thức dưới đây từ hệ thống Rentzy, hãy trả lời câu hỏi của khách hàng "
        "một cách lịch sự, tự nhiên, thân thiện (xưng 'Rentzy' hoặc 'mình', gọi khách là 'Nàng' hoặc 'khách hàng').\n\n"
        "[Yêu cầu phong cách & Trình bày]:\n"
        f"{greeting_instruction}\n"
        "- Trả lời NGẮN GỌN, TRỰC TIẾP vào câu hỏi, TUYỆT ĐỐI KHÔNG viết đoạn văn dài dòng hay lan man.\n"
        "- Độ dài lý tưởng: Chỉ từ 2-4 dòng hoặc 2-3 gạch đầu dòng (-) súc tích nhất để giải đáp ngay thắc mắc của Nàng.\n"
        "- Khi liệt kê các ý/quyền lợi/chi tiết, BẮT BUỘC dùng dấu gạch đầu dòng (-) ở đầu mỗi ý.\n"
        "- Khi nhắc đến Hotline (0798969040) hoặc Địa chỉ Showroom (51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh), "
        "hãy tách rõ ràng trên dòng riêng để khách dễ nhận diện.\n"
        "- Tuyệt đối hạn chế/không sử dụng các icon lấp lánh như ✨, emoji hoa lá trang trí không cần thiết trong câu trả lời.\n\n"
        f"[Thông tin chính thức Rentzy]:\n{context_str}\n\n"
        f"[Câu hỏi của khách hàng]: \"{state['message']}\"\n"
    )

    from app.services.llm import llm_service
    try:
        res = llm_service.generate_content(contents=prompt)
        reply = res.text.strip()
    except Exception as e:
        logger.error("Lỗi tổng hợp câu trả lời (%s)", e)
        reply = context_texts[0] if context_texts else "Rentzy xin chào Nàng! Nàng cần hỗ trợ thông tin gì ạ?"

    if not is_first_turn:
        reply = strip_opening_greeting(reply)

    logger.info("[Supervisor:Worker] Xử lý câu hỏi qua [GeneralKnowledgeNode]")
    return {
        "reply_message": reply,
        "sources": sources,
        "fallback_count": 0,
        "suggest_sales": False,
        "suggested_options": None,
        "handled_by": "general_knowledge_agent",
    }


# ---------------------------------------------------------------------------
# Node 3: Ask Clarification
# ---------------------------------------------------------------------------
def ask_clarification_node(state: AgentState) -> Dict[str, Any]:
    """Sinh câu hỏi làm rõ nhu cầu khi yêu cầu mơ hồ hoặc có nhiều ý định."""
    logger.info("[Supervisor:Worker] Yêu cầu mơ hồ -> Kích hoạt [ClarificationNode]")
    options = state.get("suggested_options") or [
        "Giới thiệu Rentzy",
        "Gói thành viên",
        "Liên hệ hỗ trợ",
    ]
    reply = (
        "Dạ Rentzy nhận thấy câu hỏi của Nàng có thể liên quan đến nhiều nội dung. "
        "Nàng vui lòng chọn hoặc làm rõ nhu cầu cụ thể bên dưới để Rentzy hỗ trợ ngay nhé:"
    )
    return {
        "reply_message": reply,
        "need_clarification": True,
        "suggest_sales": False,
        "suggested_options": options,
        "handled_by": "supervisor_clarification",
    }


# ---------------------------------------------------------------------------
# Node 4: Handle Fallback
# ---------------------------------------------------------------------------
def handle_fallback_node(state: AgentState) -> Dict[str, Any]:
    """Xử lý khi độ tin cậy thấp hoặc không hiểu nhu cầu."""
    current_count = session_service.increment_fallback_count(state["session_id"])
    logger.info("[Supervisor:Worker] Độ tin cậy thấp -> [FallbackNode] (lần %d)", current_count)

    if current_count >= 2:
        reply = (
            "Dạ Rentzy chưa hiểu chính xác ý của Nàng. Để hỗ trợ nhanh nhất, Nàng có thể kết nối với chuyên viên tư vấn qua:\n\n"
            "- Hotline tư vấn: 0798969040\n"
            "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
        )
        return {"reply_message": reply, "suggest_sales": True, "fallback_count": current_count, "suggested_options": None, "handled_by": "supervisor_fallback"}

    reply = (
        "Dạ Rentzy chưa hiểu rõ câu hỏi này của Nàng lắm. "
        "Nàng có thể hỏi lại ngắn gọn hơn hoặc cho Rentzy biết Nàng đang cần hỗ trợ về "
        "dịch vụ thuê đồ, gói thành viên hay chính sách nào được không ạ?"
    )
    return {"reply_message": reply, "suggest_sales": False, "fallback_count": current_count, "suggested_options": None, "handled_by": "supervisor_fallback"}


# ---------------------------------------------------------------------------
# Node 5: Contact Sales
# ---------------------------------------------------------------------------
def contact_sales_node(state: AgentState) -> Dict[str, Any]:
    """Xử lý Intent Liên hệ Sales."""
    session_service.reset_fallback_count(state["session_id"])
    logger.info("[Supervisor:Worker] Yêu cầu liên hệ -> [ContactSalesNode]")
    reply = (
        "Dạ Nàng! Để được tư vấn trực tiếp từ đội ngũ Rentzy, Nàng có thể liên hệ qua:\n\n"
        "- Hotline CSKH & Sales: 0798969040\n"
        "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
    )
    return {"reply_message": reply, "suggest_sales": True, "fallback_count": 0, "suggested_options": None, "handled_by": "support_sales_agent"}


# ---------------------------------------------------------------------------
# Node 6: Out of Scope
# ---------------------------------------------------------------------------
def out_of_scope_node(state: AgentState) -> Dict[str, Any]:
    """Xử lý các câu hỏi ngoài phạm vi."""
    current_count = session_service.increment_fallback_count(state["session_id"])
    logger.info("[Supervisor:Worker] Ngoài phạm vi -> [OutOfScopeGuardrail] (lần %d)", current_count)

    if current_count >= 2:
        reply = (
            "Dạ Rentzy nhận thấy câu hỏi của Nàng nằm ngoài phạm vi tự động của hệ thống. "
            "Nàng có thể liên hệ trực tiếp với chuyên viên tư vấn qua:\n\n"
            "- Hotline tư vấn: 0798969040\n"
            "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
        )
        return {"reply_message": reply, "suggest_sales": True, "fallback_count": current_count, "suggested_options": None, "handled_by": "supervisor_guardrail"}

    reply = (
        "Dạ Rentzy là tủ đồ thời trang cho thuê, hiện tại mình chỉ hỗ trợ các câu hỏi liên quan đến "
        "sản phẩm, dịch vụ và chính sách của Rentzy thôi ạ. "
        "Nàng có cần tìm hiểu về thuê váy đi tiệc, gói membership hay chính sách cọc đồ không ạ?"
    )
    return {"reply_message": reply, "suggest_sales": False, "fallback_count": current_count, "suggested_options": None, "handled_by": "supervisor_guardrail"}


# ---------------------------------------------------------------------------
# Node 7: Upcoming Feature
# ---------------------------------------------------------------------------
def upcoming_feature_node(state: AgentState) -> Dict[str, Any]:
    """Xử lý các tính năng/intent đang trong kế hoạch phát triển (Upcoming)."""
    session_service.reset_fallback_count(state["session_id"])
    intent_info = INTENT_CATALOG.get(state["intent"], {})
    title = intent_info.get("title", state["intent"])
    logger.info("[Supervisor:Worker] Tính năng đang phát triển -> [UpcomingFeatureNode] ('%s')", title)

    suggested = ["Giới thiệu về Rentzy", "Xem các gói Membership", "Gặp chuyên viên tư vấn"]
    reply = (
        f"Dạ Nàng ơi! Tính năng **{title}** hiện đang được Rentzy hoàn thiện và sẽ sớm ra mắt (**Upcoming**) ạ.\n\n"
        "Trong thời gian này, Nàng có thể tham khảo thông tin giới thiệu dịch vụ, các gói hội viên Membership, hoặc liên hệ nhân viên hỗ trợ CSKH của Rentzy nhé!"
    )
    return {
        "reply_message": reply,
        "sources": [],
        "fallback_count": 0,
        "suggest_sales": False,
        "suggested_options": suggested,
        "handled_by": "supervisor_upcoming",
    }


# ---------------------------------------------------------------------------
# Cấu hình kích hoạt các Sub-Agents
# Hiện tại: Chỉ Overview, Membership và Support hoạt động. Các agent còn lại tạm thời để upcoming.
# ---------------------------------------------------------------------------
ENABLE_POLICY_AGENT = False   # Tạm thời để upcoming theo yêu cầu
ENABLE_CATALOG_AGENT = False  # Tạm thời để upcoming theo yêu cầu


# ---------------------------------------------------------------------------
# Router Logic
# ---------------------------------------------------------------------------
def route_next_step(state: AgentState) -> str:
    # 1. Guardrails & Fallbacks (ưu tiên kiểm tra tính mơ hồ và độ tin cậy thấp trước)
    if state["intent"] == IntentEnum.FALLBACK.value:
        target = "out_of_scope"
    elif state.get("confidence", 0) < 0.70:
        target = "fallback"
    elif state.get("need_clarification") and state.get("confidence", 0) < 0.90:
        target = "clarification"
    # 2. Các Sub-Agents đang hoạt động chính thức
    elif state["intent"] == IntentEnum.MEMBERSHIP.value:
        target = "membership_agent"
    elif state["intent"] in (IntentEnum.RENTZY_OVERVIEW.value, IntentEnum.SHOWROOM_FITTING.value):
        target = "overview_agent"
    elif state["intent"] in (IntentEnum.CONTACT_SUPPORT.value, IntentEnum.ORDER_SUPPORT.value):
        target = "support_agent"
    # 3. Các Sub-Agents tạm thời chuyển sang Upcoming
    elif state["intent"] in (
        IntentEnum.DEPOSIT_POLICY.value,
        IntentEnum.DEPOSIT_REFUND.value,
        IntentEnum.RENTAL_PRICING.value,
        IntentEnum.RECEIVE_RETURN.value,
    ):
        target = "policy_agent" if ENABLE_POLICY_AGENT else "upcoming_feature"
    elif state["intent"] in (
        IntentEnum.PRODUCT_SEARCH.value,
        IntentEnum.PRODUCT_PRICE.value,
        IntentEnum.RENT_OR_LIQUIDATION.value,
        IntentEnum.LIQUIDATION.value,
    ):
        target = "catalog_agent" if ENABLE_CATALOG_AGENT else "upcoming_feature"
    else:
        target = "upcoming_feature"

    logger.info("[Supervisor:Router] Điều hướng đến Target Node: [%s]", target)
    return target


def route_entry(state: AgentState) -> str:
    """
    Điều hướng ở cửa ngõ đầu vào:
    - Nếu là câu chào đơn giản (hello, xin chào, alo...) -> kích hoạt Fast Reply tức thì (< 5ms, Zero LLM).
    - Ngược lại -> chuyển sang Classifier và các Agent chuyên biệt.
    """
    if state.get("is_greeting"):
        return "fast_reply_greeting"
    return "classify"


# ---------------------------------------------------------------------------
# Build & Compile Main Dialogue Graph
# ---------------------------------------------------------------------------
def build_dialogue_graph():
    workflow = StateGraph(AgentState)

    # Inbound & Fast-Reply Nodes
    workflow.add_node("preprocess", preprocess_input_node)
    workflow.add_node("fast_reply_greeting", fast_reply_greeting_node)

    # Core & Sub-Agent Nodes
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("membership_agent", membership_agent_node)
    workflow.add_node("overview_agent", overview_agent_node)
    workflow.add_node("support_agent", support_agent_node)
    workflow.add_node("policy_agent", policy_agent_node)
    workflow.add_node("catalog_agent", catalog_agent_node)
    workflow.add_node("retrieve_knowledge", retrieve_knowledge_node)
    workflow.add_node("clarification", ask_clarification_node)
    workflow.add_node("fallback", handle_fallback_node)
    workflow.add_node("contact_sales", contact_sales_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("upcoming_feature", upcoming_feature_node)

    # Entry point is preprocess
    workflow.set_entry_point("preprocess")

    # Conditional routing from preprocess
    workflow.add_conditional_edges(
        "preprocess",
        route_entry,
        {
            "fast_reply_greeting": "fast_reply_greeting",
            "classify": "classify",
        },
    )

    # Fast reply leads directly to END (No LLM called)
    workflow.add_edge("fast_reply_greeting", END)

    # Conditional routing from classify
    workflow.add_conditional_edges(
        "classify",
        route_next_step,
        {
            "membership_agent":  "membership_agent",
            "overview_agent":    "overview_agent",
            "support_agent":     "support_agent",
            "policy_agent":      "policy_agent",
            "catalog_agent":     "catalog_agent",
            "contact_sales":     "contact_sales",
            "out_of_scope":      "out_of_scope",
            "clarification":     "clarification",
            "fallback":          "fallback",
            "upcoming_feature":  "upcoming_feature",
            "retrieve_knowledge": "retrieve_knowledge",
        },
    )

    # All terminal nodes → END
    workflow.add_edge("membership_agent", END)
    workflow.add_edge("overview_agent", END)
    workflow.add_edge("support_agent", END)
    workflow.add_edge("policy_agent", END)
    workflow.add_edge("catalog_agent", END)
    workflow.add_edge("retrieve_knowledge", END)
    workflow.add_edge("clarification", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("contact_sales", END)
    workflow.add_edge("out_of_scope", END)
    workflow.add_edge("upcoming_feature", END)

    return workflow.compile()


dialogue_graph = build_dialogue_graph()
