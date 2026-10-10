import pytest
from app.graph.dialogue_graph import dialogue_graph, AgentState
from app.services.session import session_service
from app.schemas.chat import SessionState
from app.core.intents import IntentEnum

def test_phase4_knowledge_retrieval_and_answer_synthesis():
    """Phase 4: Kiểm tra Node retrieve_knowledge truy xuất RAG Story 1 và tổng hợp câu trả lời."""
    session_id = "phase4_rag_sess"
    session_service.save_session(SessionState(session_id=session_id))

    # Gửi câu hỏi rõ ràng về Rentzy overview
    initial_state = {
        "session_id": session_id,
        "message": "Giới thiệu cho mình về Rentzy",
        "chat_history": [],
        "intent": "",
        "intent_title": "",
        "confidence": 0.0,
        "need_clarification": False,
        "suggest_sales": False,
        "suggested_options": None,
        "reply_message": "",
        "fallback_count": 0,
        "sources": None
    }

    final_state = dialogue_graph.invoke(initial_state)

    assert final_state["intent"] == IntentEnum.RENTZY_OVERVIEW.value
    assert len(final_state["reply_message"]) > 0
    assert final_state["fallback_count"] == 0
    assert final_state["suggest_sales"] is False
    assert final_state["sources"] is not None
    assert len(final_state["sources"]) > 0

def test_phase4_sales_escalation_after_2_failed_attempts():
    """Phase 4: Kiểm tra quy tắc đếm 2 lần không hiểu liên tiếp tự động chuyển Sales Agent."""
    from app.graph.dialogue_graph import handle_fallback_node

    session_id = "phase4_sales_escalation_sess"
    session_service.save_session(SessionState(session_id=session_id, fallback_count=0))

    state: AgentState = {
        "session_id": session_id,
        "message": "câu hỏi mơ hồ low confidence",
        "chat_history": [],
        "intent": IntentEnum.DEPOSIT_POLICY.value,
        "intent_title": "Chính sách",
        "confidence": 0.40,
        "need_clarification": False,
        "suggest_sales": False,
        "suggested_options": None,
        "reply_message": "",
        "fallback_count": 0,
        "sources": None
    }

    # Lần 1 không hiểu -> fallback_count = 1, chưa suggest sales
    res1 = handle_fallback_node(state)
    assert res1["fallback_count"] == 1
    assert res1["suggest_sales"] is False
    assert "chưa hiểu rõ" in res1["reply_message"]

    # Lần 2 không hiểu liên tiếp -> fallback_count = 2, suggest sales = True
    res2 = handle_fallback_node(state)
    assert res2["fallback_count"] == 2
    assert res2["suggest_sales"] is True
    assert "0798969040" in res2["reply_message"] or "Sales" in res2["reply_message"]

def test_phase4_direct_contact_sales_intent():
    """Phase 4: Kiểm tra Intent trực tiếp gặp Sales (contact_support)."""
    session_id = "phase4_direct_sales_sess"
    session_service.save_session(SessionState(session_id=session_id))

    state_sales = dialogue_graph.invoke({
        "session_id": session_id,
        "message": "Cho mình xin số hotline cskh",
        "chat_history": [],
        "intent": "", "intent_title": "", "confidence": 0.0,
        "need_clarification": False, "suggest_sales": False,
        "suggested_options": None, "reply_message": "", "fallback_count": 0, "sources": None
    })

    assert state_sales["intent"] == IntentEnum.CONTACT_SUPPORT.value
    assert state_sales["suggest_sales"] is True
    assert "0798969040" in state_sales["reply_message"]
    assert state_sales["fallback_count"] == 0
