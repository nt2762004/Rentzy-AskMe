"""
Unit tests for unified LLMService and automatic failover across 4 chosen Gemini models.
"""

from unittest.mock import MagicMock, patch
from app.services.llm import llm_service
from app.core.config import settings


def test_model_pool_order():
    """Kiểm tra danh sách 4 model theo đúng thứ tự ưu tiên mà người dùng đã chỉ định."""
    pool = llm_service.get_model_pool()
    expected = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.8-flash",
    ]
    assert pool == expected


def test_llm_service_failover_on_503():
    """Kiểm tra khi model đầu tiên bị 503 UNAVAILABLE, hệ thống tự động chuyển sang model thứ 2."""
    mock_client = MagicMock()

    # Model 1 (gemini-3.1-flash-lite) ném lỗi 503
    # Model 2 (gemini-3.5-flash-lite) phản hồi thành công
    mock_response = MagicMock()
    mock_response.text = "Phản hồi từ model dự phòng"

    def side_effect(model, contents, config=None):
        if model == "gemini-3.1-flash-lite":
            raise Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
        return mock_response

    mock_client.models.generate_content.side_effect = side_effect

    with patch.object(llm_service, "_client", mock_client):
        res = llm_service.generate_content("Test câu hỏi")
        assert res.text == "Phản hồi từ model dự phòng"
        # Đã gọi lần 1 với 3.1 và lần 2 với 3.5
        assert mock_client.models.generate_content.call_count == 2
        calls = mock_client.models.generate_content.call_args_list
        assert calls[0].kwargs["model"] == "gemini-3.1-flash-lite"
        assert calls[1].kwargs["model"] == "gemini-3.5-flash-lite"


def test_llm_service_chat_failover_on_429():
    """Kiểm tra khi chat gặp 429 RATE_LIMIT, tự động chuyển sang model tiếp theo."""
    mock_client = MagicMock()

    mock_res_ok = MagicMock()
    mock_res_ok.text = "Chat thành công từ model dự phòng"

    mock_chat_ok = MagicMock()
    mock_chat_ok.send_message.return_value = mock_res_ok

    def chat_side_effect(model, config=None):
        if model == "gemini-3.1-flash-lite":
            raise Exception("429 RESOURCE_EXHAUSTED. Rate limit exceeded.")
        return mock_chat_ok

    mock_client.chats.create.side_effect = chat_side_effect

    with patch.object(llm_service, "_client", mock_client):
        reply = llm_service.send_chat_message("Test chat")
        assert reply == "Chat thành công từ model dự phòng"
        assert mock_client.chats.create.call_count == 2
