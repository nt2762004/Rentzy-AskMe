import pytest
from app.core.intents import IntentEnum, INTENT_CATALOG, ABBREVIATION_MAP, INTENT_TO_TOPIC_MAP
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, SessionState

def test_phase1_all_12_intents_defined():
    """Kiểm tra đầy đủ 14 Intent được định nghĩa trong IntentEnum và INTENT_CATALOG."""
    assert len(IntentEnum) == 14
    assert len(INTENT_CATALOG) == 14

    for intent in IntentEnum:
        code = intent.value
        assert code in INTENT_CATALOG
        info = INTENT_CATALOG[code]
        assert "title" in info
        assert "description" in info
        assert "keywords" in info
        assert len(info["examples"]) > 0

def test_phase1_abbreviation_map():
    """Kiểm tra từ điển chuẩn hóa từ viết tắt."""
    assert ABBREVIATION_MAP["cọc"] == "đặt cọc"
    assert ABBREVIATION_MAP["tly"] == "thanh lý"
    assert ABBREVIATION_MAP["sm"] == "showroom"
    assert ABBREVIATION_MAP["cskh"] == "chăm sóc khách hàng"

def test_phase1_intent_to_topic_mapping():
    """Kiểm tra ánh xạ giữa 14 Intent và các Topic trong Story 1 CSDL."""
    for intent in IntentEnum:
        assert intent.value in INTENT_TO_TOPIC_MAP
        assert isinstance(INTENT_TO_TOPIC_MAP[intent.value], str)


def test_phase1_pydantic_chat_schemas():
    """Kiểm tra validation của ChatRequest, ChatResponse, và SessionState."""
    req = ChatRequest(session_id="sess-123", message="Rentzy là gì?")
    assert req.session_id == "sess-123"
    assert req.message == "Rentzy là gì?"

    res = ChatResponse(
        session_id="sess-123",
        intent="rentzy_overview",
        intent_title="Giới thiệu Rentzy",
        confidence=0.95,
        reply_message="Rentzy là tủ đồ thời trang...",
        need_clarification=False,
        suggest_sales=False
    )
    assert res.intent == "rentzy_overview"
    assert res.confidence == 0.95

    session = SessionState(session_id="sess-123")
    assert session.fallback_count == 0
    assert len(session.messages) == 0
