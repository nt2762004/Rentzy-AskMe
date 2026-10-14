import pytest
from app.graph.dialogue_graph import (
    dialogue_graph,
    route_next_step,
    AgentState,
    ask_clarification_node,
    handle_fallback_node,
    contact_sales_node,
    out_of_scope_node
)
from app.core.intents import IntentEnum
from app.services.session import session_service
from app.schemas.chat import SessionState

def test_phase2_graph_compiled():
    """Kiểm tra LangGraph StateGraph được khởi tạo và biên dịch thành công."""
    assert dialogue_graph is not None
    # Kiểm tra các node tồn tại trong compiled graph
    node_names = set(dialogue_graph.nodes.keys())
    expected_nodes = {"classify", "retrieve_knowledge", "clarification", "fallback", "contact_sales", "out_of_scope"}
    assert expected_nodes.issubset(node_names)

def test_phase2_routing_logic():
    """Kiểm tra logic rẽ nhánh Router (route_next_step)."""
    # 1. Intent Contact Support -> contact_sales node
    state1: AgentState = {
        "session_id": "test_sess", "message": "Gặp CSKH", "chat_history": [],
        "intent": IntentEnum.CONTACT_SUPPORT.value, "intent_title": "Liên hệ Sales",
        "confidence": 0.95, "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    }
    assert route_next_step(state1) == "support_agent"

    # 2. Intent Fallback -> out_of_scope node
    state2: AgentState = {
        "session_id": "test_sess", "message": "Thời tiết hôm nay", "chat_history": [],
        "intent": IntentEnum.FALLBACK.value, "intent_title": "Ngoài phạm vi",
        "confidence": 0.95, "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    }
    assert route_next_step(state2) == "out_of_scope"

    # 3. Need Clarification + confidence < 0.90 -> clarification node
    state3: AgentState = {
        "session_id": "test_sess", "message": "Tôi muốn thuê", "chat_history": [],
        "intent": IntentEnum.PRODUCT_SEARCH.value, "intent_title": "Thuê đồ",
        "confidence": 0.80, "need_clarification": True, "suggest_sales": False,
        "suggested_options": ["Thuê đồ tiệc", "Thuê đồ cưới"], "reply_message": "", "fallback_count": 0, "sources": None
    }
    assert route_next_step(state3) == "clarification"

    # 4. Low Confidence (< 0.70) -> fallback node
    state4: AgentState = {
        "session_id": "test_sess", "message": "abcxyz", "chat_history": [],
        "intent": IntentEnum.FALLBACK.value, "intent_title": "Chưa rõ",
        "confidence": 0.50, "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    }
    state4_domain: AgentState = {**state4, "intent": IntentEnum.DEPOSIT_POLICY.value}
    assert route_next_step(state4_domain) == "fallback"

    # 5. High Confidence (>= 0.70) -> retrieve_knowledge node
    state5: AgentState = {
        "session_id": "test_sess", "message": "Rentzy là gì?", "chat_history": [],
        "intent": IntentEnum.RENTZY_OVERVIEW.value, "intent_title": "Giới thiệu Rentzy",
        "confidence": 0.95, "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    }
    assert route_next_step(state5) == "overview_agent"

def test_phase2_node_outputs():
    """Kiểm tra phản hồi và biến trạng thái sinh ra từ các Node."""
    session_id = "phase2_node_test_sess"
    session_service.save_session(SessionState(session_id=session_id))

    # Test Contact Sales Node
    state: AgentState = {
        "session_id": session_id, "message": "Muốn gặp tư vấn", "chat_history": [],
        "intent": IntentEnum.CONTACT_SUPPORT.value, "intent_title": "Liên hệ Sales",
        "confidence": 0.95, "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    }
    res_sales = contact_sales_node(state)
    assert res_sales["suggest_sales"] is True
    assert "0798969040" in res_sales["reply_message"]

    # Test Out of Scope Node
    res_oos = out_of_scope_node(state)
    assert res_oos["suggest_sales"] is False
    assert "chỉ hỗ trợ các câu hỏi liên quan đến sản phẩm" in res_oos["reply_message"]

    # Test Clarification Node
    res_clarify = ask_clarification_node(state)
    assert res_clarify["need_clarification"] is True
    assert "Nàng vui lòng chọn hoặc làm rõ" in res_clarify["reply_message"]

    # Test Fallback Node (Increment count)
    session_service.save_session(SessionState(session_id=session_id, fallback_count=0))
    res_fb1 = handle_fallback_node(state)
    assert res_fb1["fallback_count"] == 1
    assert res_fb1["suggest_sales"] is False

    res_fb2 = handle_fallback_node(state)
    assert res_fb2["fallback_count"] == 2
    assert res_fb2["suggest_sales"] is True
