import logging
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.intents import INTENT_CATALOG, IntentEnum, INTENT_TO_TOPIC_MAP
from app.services.classifier import intent_classifier
from app.services.session import session_service
from app.services.search import search_service
from app.schemas.knowledge import SearchRequest, SearchFilter

logger = logging.getLogger(__name__)

# 1. Định nghĩa AgentState cho LangGraph
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

# 2. Định nghĩa các Node trong LangGraph

def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Phân loại ý định của tin nhắn người dùng."""
    session = session_service.get_session(state["session_id"])
    chat_history_dicts = [m.model_dump() for m in session.messages]

    result = intent_classifier.classify(state["message"], chat_history=chat_history_dicts)
    intent_info = INTENT_CATALOG.get(result.intent, {})

    session.current_intent = result.intent
    session_service.save_session(session)

    return {
        "intent": result.intent,
        "intent_title": intent_info.get("title", "Không xác định"),
        "confidence": result.confidence,
        "need_clarification": result.need_clarification,
        "suggested_options": result.suggested_options,
        "fallback_count": session.fallback_count
    }

def retrieve_knowledge_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Lấy tri thức từ Story 1 Search Service và tổng hợp câu trả lời."""
    # Reset fallback counter vì đã hiểu intent
    session_service.reset_fallback_count(state["session_id"])

    # Mapping intent sang topic của Story 1 (khớp 1-1 với 14 topic Excel)
    topic_filter = INTENT_TO_TOPIC_MAP.get(state["intent"], state["intent"])
    if topic_filter == "fallback":
        topic_filter = None


    search_req = SearchRequest(
        query=state["message"],
        top_k=3,
        filter=SearchFilter(
            status="active",
            topic=topic_filter
        )
    )

    search_res = search_service.search_knowledge(search_req)

    # Nếu không tìm thấy kết quả từ topic filter, tìm kiếm tự do trên active status
    if search_res.total_results == 0 and topic_filter:
        search_req.filter.topic = None
        search_res = search_service.search_knowledge(search_req)

    context_texts = []
    sources = []
    for item in search_res.results:
        context_texts.append(f"- {item.content}")
        sources.append({
            "chunk_id": item.chunk_id,
            "document_id": item.metadata.document_id,
            "record_id": item.metadata.record_id,
            "score": item.score,
            "source_url": item.metadata.source_url
        })

    context_str = "\n".join(context_texts) if context_texts else "Chưa tìm thấy bài viết chi tiết trong hệ thống."

    # Tổng hợp câu trả lời bằng Gemini Flash Lite
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    membership_instruction = ""
    if state["intent"] == IntentEnum.MEMBERSHIP.value:
        membership_instruction = """
- QUY TẮC BẮT BUỘC VỀ MEMBERSHIP: Vì khách hàng đang hỏi về Gói thành viên (Membership), ở cuối câu trả lời, bạn BẮT BUỘC phải đề cập và hướng dẫn khách hàng truy cập đường link chính thức sau để tham khảo chi tiết bảng quyền lợi và đăng ký: https://rentzy.vn/member-ship/
(Ví dụ: 'Nàng có thể tham khảo chi tiết quyền lợi và đăng ký gói tại đây nhé: https://rentzy.vn/member-ship/')."""

    prompt = f"""Bạn là Trợ lý AI AskMe của thương hiệu thời trang Rentzy.
Dựa vào ngữ cảnh thông tin chính thức dưới đây từ hệ thống Rentzy, hãy trả lời câu hỏi của khách hàng một cách lịch sự, tự nhiên, thân thiện (xưng 'Rentzy' hoặc 'mình', gọi khách là 'Nàng' hoặc 'khách hàng').

[Yêu cầu phong cách & Trình bày]:
- Trả lời NGẮN GỌN, TRỰC TIẾP vào câu hỏi, TUYỆT ĐỐI KHÔNG viết đoạn văn dài dòng hay lan man.
- Độ dài lý tưởng: Chỉ từ 2-4 dòng hoặc 2-3 gạch đầu dòng (-) súc tích nhất để giải đáp ngay thắc mắc của Nàng.
- Khi liệt kê các ý/quyền lợi/chi tiết, BẮT BUỘC dùng dấu gạch đầu dòng (-) ở đầu mỗi ý.
- Khi nhắc đến Hotline (0798969040) hoặc Địa chỉ Showroom (51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh), hãy tách rõ ràng trên dòng riêng để khách dễ nhận diện.
- Tuyệt đối hạn chế/không sử dụng các icon lấp lánh như ✨, emoji hoa lá trang trí không cần thiết trong câu trả lời. Giữ phong cách thời trang thanh lịch, tinh tế.{membership_instruction}

[Thông tin chính thức Rentzy]:
{context_str}

[Câu hỏi của khách hàng]: "{state['message']}"
"""

    try:
        res = client.models.generate_content(
            model=settings.LLM_MODEL_NAME,
            contents=prompt
        )
        reply = res.text.strip()
    except Exception as e:
        logger.error(f"Lỗi tổng hợp câu trả lời ({e})")
        reply = context_texts[0] if context_texts else "Rentzy xin chào Nàng! Nàng cần hỗ trợ thông tin gì ạ?"

    # Đảm bảo 100% luôn có link https://rentzy.vn/member-ship/ khi hỏi về membership
    if state["intent"] == IntentEnum.MEMBERSHIP.value and "https://rentzy.vn/member-ship/" not in reply:
        reply += "\n\nNàng có thể tham khảo chi tiết bảng quyền lợi và đăng ký gói tại đây nhé: https://rentzy.vn/member-ship/"

    suggested_options = get_contextual_suggested_options(state["intent"], state["message"])

    return {
        "reply_message": reply,
        "sources": sources,
        "fallback_count": 0,
        "suggest_sales": False,
        "suggested_options": suggested_options
    }

def get_contextual_suggested_options(intent: str, message: str = "") -> List[str]:
    """Trả về danh sách 3-4 lựa chọn gợi ý phù hợp cho từng câu trả lời, gắn nhãn (Upcoming) nếu tính năng chưa mở."""
    if intent == IntentEnum.MEMBERSHIP.value:
        return [
            "Quyền lợi gói Silver & Gold",
            "Giới thiệu Rentzy",
            "Tìm trang phục (Upcoming)",
            "Chính sách cọc đồ (Upcoming)"
        ]
    elif intent == IntentEnum.RENTZY_OVERVIEW.value:
        return [
            "Gói thành viên",
            "Địa chỉ Showroom",
            "Tìm trang phục (Upcoming)",
            "Xem giá và lịch thuê (Upcoming)"
        ]
    elif intent in (IntentEnum.PRODUCT_SEARCH.value, IntentEnum.PRODUCT_PRICE.value):
        return [
            "Giới thiệu Rentzy",
            "Gói thành viên",
            "Xem giá và lịch thuê (Upcoming)",
            "Liên hệ CSKH"
        ]
    elif intent in (IntentEnum.RENTAL_PRICING.value, IntentEnum.DEPOSIT_POLICY.value, IntentEnum.DEPOSIT_REFUND.value):
        return [
            "Gói thành viên",
            "Giới thiệu Rentzy",
            "Tìm trang phục (Upcoming)",
            "Liên hệ CSKH"
        ]
    elif intent == IntentEnum.CONTACT_SUPPORT.value:
        return [
            "Giới thiệu Rentzy",
            "Gói thành viên",
            "Tìm trang phục (Upcoming)"
        ]
    else:
        return [
            "Giới thiệu Rentzy",
            "Gói thành viên",
            "Tìm trang phục (Upcoming)",
            "Chính sách thuê đồ (Upcoming)"
        ]

def ask_clarification_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Sinh câu hỏi làm rõ nhu cầu khi yêu cầu mơ hồ hoặc có nhiều ý định."""
    options = state.get("suggested_options") or [
        "Giới thiệu Rentzy",
        "Gói thành viên",
        "Chính sách đặt cọc (Upcoming)"
    ]

    reply = "Dạ Rentzy nhận thấy câu hỏi của Nàng có thể liên quan đến nhiều nội dung. Nàng chọn nhu cầu cụ thể bên dưới để Rentzy hỗ trợ ngay nhé:"

    return {
        "reply_message": reply,
        "need_clarification": True,
        "suggest_sales": False,
        "suggested_options": options
    }

def handle_fallback_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Xử lý khi độ tin cậy thấp hoặc không hiểu nhu cầu. Đếm số lần thất bại."""
    current_count = session_service.increment_fallback_count(state["session_id"])
    suggested_options = [
        "Giới thiệu Rentzy",
        "Gói thành viên",
        "Tìm trang phục (Upcoming)",
        "Liên hệ CSKH"
    ]

    if current_count >= 2:
        reply = (
            "Dạ Rentzy chưa hiểu chính xác ý của Nàng. Để hỗ trợ nhanh nhất, Nàng có thể kết nối với chuyên viên tư vấn qua:\n\n"
            "- Hotline tư vấn: 0798969040\n"
            "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
        )
        return {
            "reply_message": reply,
            "suggest_sales": True,
            "fallback_count": current_count,
            "suggested_options": suggested_options
        }

    reply = "Dạ Rentzy chưa hiểu rõ câu hỏi này của Nàng lắm. Nàng có thể hỏi lại ngắn gọn hơn hoặc chọn các gợi ý bên dưới nhé!"
    return {
        "reply_message": reply,
        "suggest_sales": False,
        "fallback_count": current_count,
        "suggested_options": suggested_options
    }

def contact_sales_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Xử lý Intent Liên hệ Sales."""
    session_service.reset_fallback_count(state["session_id"])
    reply = (
        "Dạ Nàng! Để được tư vấn trực tiếp từ đội ngũ Rentzy, Nàng có thể liên hệ qua:\n\n"
        "- Hotline CSKH & Sales: 0798969040\n"
        "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
    )
    return {
        "reply_message": reply,
        "suggest_sales": True,
        "fallback_count": 0,
        "suggested_options": [
            "Giới thiệu Rentzy",
            "Gói thành viên",
            "Tìm trang phục (Upcoming)"
        ]
    }

def out_of_scope_node(state: AgentState) -> Dict[str, Any]:
    """Node 6: Xử lý các câu hỏi ngoài phạm vi. Tự động đề xuất Sales nếu lặp lại 2 lần."""
    current_count = session_service.increment_fallback_count(state["session_id"])
    suggested_options = [
        "Giới thiệu Rentzy",
        "Gói thành viên",
        "Tìm trang phục (Upcoming)",
        "Liên hệ CSKH"
    ]

    if current_count >= 2:
        reply = (
            "Dạ Rentzy nhận thấy câu hỏi của Nàng nằm ngoài phạm vi tự động của hệ thống. Nàng có thể liên hệ trực tiếp với chuyên viên tư vấn qua:\n\n"
            "- Hotline tư vấn: 0798969040\n"
            "- Địa chỉ Showroom: 51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
        )
        return {
            "reply_message": reply,
            "suggest_sales": True,
            "fallback_count": current_count,
            "suggested_options": suggested_options
        }

    reply = "Dạ Rentzy là tủ đồ thời trang cho thuê, hiện tại mình chỉ hỗ trợ giải đáp về dịch vụ và ưu đãi của Rentzy thôi ạ. Nàng có thể tham khảo các gợi ý bên dưới nhé!"
    return {
        "reply_message": reply,
        "suggest_sales": False,
        "fallback_count": current_count,
        "suggested_options": suggested_options
    }

# 3. Danh sách các Intent đang mở thử nghiệm (Active Intents)
ACTIVE_INTENTS = {
    IntentEnum.RENTZY_OVERVIEW.value,
    IntentEnum.MEMBERSHIP.value,
}

def upcoming_feature_node(state: AgentState) -> Dict[str, Any]:
    """Node xử lý các tính năng/intent đang trong kế hoạch phát triển (Upcoming)."""
    session_service.reset_fallback_count(state["session_id"])
    intent_info = INTENT_CATALOG.get(state["intent"], {})
    title = intent_info.get("title", state["intent"])

    reply = (
        f"Dạ Nàng ơi! Tính năng **{title}** hiện đang được Rentzy phát triển và sẽ sớm ra mắt (**Upcoming**) ạ.\n\n"
        "Nàng có thể tham khảo trước thông tin dịch vụ hoặc gói hội viên bên dưới nhé!"
    )

    suggested_options = get_contextual_suggested_options(state["intent"], state["message"])

    return {
        "reply_message": reply,
        "sources": [],
        "fallback_count": 0,
        "suggest_sales": False,
        "suggested_options": suggested_options
    }

# 4. Định nghĩa rẽ nhánh điều kiện (Router Logic)
def route_next_step(state: AgentState) -> str:
    # Nếu intent là contact_support -> Chuyển node sales
    if state["intent"] == IntentEnum.CONTACT_SUPPORT.value:
        return "contact_sales"

    # Nếu intent là fallback -> Chuyển node out_of_scope
    if state["intent"] == IntentEnum.FALLBACK.value:
        return "out_of_scope"

    # Nếu cần làm rõ ý định (multi-intent / mơ hồ) -> Chuyển node clarification
    if state.get("need_clarification") and state.get("confidence", 0) < 0.90:
        return "clarification"

    # Nếu độ tin cậy thấp < 0.70 -> Chuyển node fallback
    if state.get("confidence", 0) < 0.70:
        return "fallback"

    # Nếu intent chưa nằm trong danh sách mở thử nghiệm -> Chuyển node upcoming_feature
    if state["intent"] not in ACTIVE_INTENTS:
        return "upcoming_feature"

    # Mặc định: Thuộc các Intent đang mở thử nghiệm -> Truy xuất tri thức Story 1
    return "retrieve_knowledge"

# 5. Xây dựng và Biên dịch StateGraph LangGraph
def build_dialogue_graph():
    workflow = StateGraph(AgentState)

    # Thêm các Node
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("retrieve_knowledge", retrieve_knowledge_node)
    workflow.add_node("clarification", ask_clarification_node)
    workflow.add_node("fallback", handle_fallback_node)
    workflow.add_node("contact_sales", contact_sales_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("upcoming_feature", upcoming_feature_node)

    # Thiết lập Điểm khởi đầu (Entry Point)
    workflow.set_entry_point("classify")

    # Thêm Rẽ nhánh Điều kiện từ Node Classify
    workflow.add_conditional_edges(
        "classify",
        route_next_step,
        {
            "contact_sales": "contact_sales",
            "out_of_scope": "out_of_scope",
            "clarification": "clarification",
            "fallback": "fallback",
            "upcoming_feature": "upcoming_feature",
            "retrieve_knowledge": "retrieve_knowledge"
        }
    )

    # Tất cả các nút kết thúc đều dẫn về END
    workflow.add_edge("retrieve_knowledge", END)
    workflow.add_edge("clarification", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("contact_sales", END)
    workflow.add_edge("out_of_scope", END)
    workflow.add_edge("upcoming_feature", END)

    return workflow.compile()

dialogue_graph = build_dialogue_graph()
