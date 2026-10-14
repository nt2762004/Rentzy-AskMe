"""
Unit & Integration tests for Greeting Fast Reply and Multi-Turn Greeting Stripping.
"""

import pytest
from app.core.greetings import (
    is_simple_greeting,
    strip_opening_greeting,
    FAST_REPLY_GREETING_MESSAGE,
    FAST_REPLY_CONTINUATION_GREETING_MESSAGE,
    FAST_REPLY_SUGGESTED_OPTIONS,
)
from app.graph.dialogue_graph import dialogue_graph
from app.services.session import session_service


# ---------------------------------------------------------------------------
# 1. Unit Tests: is_simple_greeting
# ---------------------------------------------------------------------------
def test_is_simple_greeting_positive():
    """Kiểm tra các câu chào hỏi đơn giản phải được nhận diện chính xác."""
    greetings = [
        "hello",
        "Hello Rentzy!",
        "hi shop",
        "Xin chào shop ạ",
        "chào bạn nha",
        "chào shop",
        "alo shop ơi",
        "shop ơi",
        "rentzy ơi ạ",
        "alooo",
        "hế nhô cả nhà",
        "hi",
        "hey",
        "chào bạn",
        "chào ad",
        "alo",
        "alo ạ",
        "ad ơi",
        "chào shop nhá",
        "chào shop nhen",
        "chào shop nhe",
    ]
    for text in greetings:
        assert is_simple_greeting(text) is True, f"Failed positive match for: '{text}'"


def test_is_simple_greeting_negative():
    """Kiểm tra các câu hỏi chứa nội dung nghiệp vụ KHÔNG được xem là câu chào đơn giản."""
    non_greetings = [
        "chào shop, gói membership giá bao nhiêu?",
        "xin chào showroom ở đâu",
        "hello mình muốn thuê đầm",
        "alo cho mình hỏi cọc đồ",
        "rentzy là gì",
        "cho mình hỏi giá thuê",
        "váy này bao nhiêu tiền",
        "các gói thành viên có những gì?",
        "Gói DC2990K là gì?",
        "Tôi muốn gặp nhân viên tư vấn",
        "Thời tiết hôm nay thế nào?",
    ]
    for text in non_greetings:
        assert is_simple_greeting(text) is False, f"Failed negative match for: '{text}'"


# ---------------------------------------------------------------------------
# 2. Unit Tests: strip_opening_greeting
# ---------------------------------------------------------------------------
def test_strip_opening_greeting():
    """Kiểm tra việc loại bỏ các câu chào mở đầu lặp lại."""
    cases = [
        (
            "Chào Nàng, Rentzy hiện có 4 gói thành viên với thời hạn 24 tháng.",
            "Rentzy hiện có 4 gói thành viên với thời hạn 24 tháng."
        ),
        (
            "Dạ chào Nàng! Rentzy hiện có các gói thành viên...",
            "Rentzy hiện có các gói thành viên..."
        ),
        (
            "Dạ chào Nàng, gói DC2990K có giá là 2.990.000đ.",
            "Gói DC2990K có giá là 2.990.000đ."
        ),
        (
            "Xin chào Nàng! Showroom Rentzy mở cửa từ 9h.",
            "Showroom Rentzy mở cửa từ 9h."
        ),
        (
            "Rentzy xin chào Nàng! Nàng có thể đến thử đồ trực tiếp.",
            "Nàng có thể đến thử đồ trực tiếp."
        ),
        (
            "Dạ Rentzy xin chào Nàng! Rentzy có các gói...",
            "Rentzy có các gói..."
        ),
        (
            "Chào Nàng ơi, gói này đã bao gồm voucher 500k.",
            "Gói này đã bao gồm voucher 500k."
        ),
        (
            "Dạ Nàng! Để được hỗ trợ trực tiếp...",
            "Để được hỗ trợ trực tiếp..."
        ),
        (
            "Dạ, Rentzy có 4 gói thành viên chính.",
            "Rentzy có 4 gói thành viên chính."
        ),
        (
            "Gói DC2990K có giá 2.990.000đ, giảm 10% giá thuê.",
            "Gói DC2990K có giá 2.990.000đ, giảm 10% giá thuê."
        ),
    ]
    for orig, expected in cases:
        stripped = strip_opening_greeting(orig)
        assert stripped == expected, f"Failed stripping: '{orig}' -> Got: '{stripped}', Expected: '{expected}'"


# ---------------------------------------------------------------------------
# 3. Integration Tests: Fast Reply Greeting through Dialogue Graph
# ---------------------------------------------------------------------------
def test_fast_reply_greeting_turn_1():
    """Lượt 1: User gửi câu chào đơn giản -> nhận ngay Fast Reply, không gọi LLM."""
    session_id = "test_greeting_fast_reply_1"
    # Thêm user message vào session store như trong api chat.py
    session_service.add_message(session_id, role="user", content="Xin chào Rentzy")

    state_input = {
        "session_id": session_id,
        "message": "Xin chào Rentzy",
    }
    output = dialogue_graph.invoke(state_input)

    assert output["handled_by"] == "fast_reply_greeting"
    assert output["confidence"] == 1.0
    assert output["reply_message"] == FAST_REPLY_GREETING_MESSAGE
    assert output["suggested_options"] == FAST_REPLY_SUGGESTED_OPTIONS


def test_fast_reply_greeting_continuation():
    """Lượt sau trong session: User gửi 'alo' -> Fast Reply với câu ngắn gọn."""
    session_id = "test_greeting_fast_reply_cont"
    # Giả lập đã có hội thoại trước
    session_service.add_message(session_id, role="user", content="Gói VIP là gì?")
    session_service.add_message(session_id, role="assistant", content="Gói VIP là gói thành viên cao cấp...")

    # Bây giờ user gửi lời chào 'alo shop ơi'
    session_service.add_message(session_id, role="user", content="alo shop ơi")
    state_input = {
        "session_id": session_id,
        "message": "alo shop ơi",
    }
    output = dialogue_graph.invoke(state_input)

    assert output["handled_by"] == "fast_reply_greeting"
    assert output["reply_message"] == FAST_REPLY_CONTINUATION_GREETING_MESSAGE


# ---------------------------------------------------------------------------
# 4. Integration Tests: Multi-Turn Greeting Suppression
# ---------------------------------------------------------------------------
def test_multi_turn_greeting_suppressed():
    """
    Kiểm tra trong 1 session đa lượt:
    Turn 1: User chào hỏi -> Fast reply chào.
    Turn 2: User hỏi về Gói thành viên -> Phản hồi KHÔNG được lặp lại câu chào ('Chào Nàng,').
    """
    session_id = "test_multi_turn_no_repeated_greeting"

    # Turn 1: Chào
    session_service.add_message(session_id, role="user", content="hello")
    out1 = dialogue_graph.invoke({"session_id": session_id, "message": "hello"})
    assert out1["handled_by"] == "fast_reply_greeting"
    session_service.add_message(session_id, role="assistant", content=out1["reply_message"])

    # Turn 2: Hỏi gói thành viên
    session_service.add_message(session_id, role="user", content="Các gói Membership thành viên tại Rentzy gồm những gì?")
    out2 = dialogue_graph.invoke({
        "session_id": session_id,
        "message": "Các gói Membership thành viên tại Rentzy gồm những gì?",
    })
    session_service.add_message(session_id, role="assistant", content=out2["reply_message"])

    reply_turn2 = out2["reply_message"]
    # Kiểm tra phản hồi ở lượt 2 TUYỆT ĐỐI không bắt đầu bằng "Chào Nàng," hay "Dạ chào Nàng"
    assert not reply_turn2.lower().startswith("chào nàng"), f"Turn 2 still starts with greeting: {reply_turn2}"
    assert not reply_turn2.lower().startswith("dạ chào nàng"), f"Turn 2 still starts with greeting: {reply_turn2}"
    assert not reply_turn2.lower().startswith("xin chào nàng"), f"Turn 2 still starts with greeting: {reply_turn2}"
    assert "DC2990" in reply_turn2 or "DC3990" in reply_turn2 or "thành viên" in reply_turn2
