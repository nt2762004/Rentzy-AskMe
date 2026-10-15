"""
Unit tests for Meta Webhook (Facebook Messenger & Instagram Direct).
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_meta_webhook_verification_success():
    """Test xác thực Webhook với Meta thành công khi đúng token."""
    response = client.get(
        "/api/v1/meta/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "rentzy_meta_2026",
            "hub.challenge": "challenge_code_987654",
        },
    )
    assert response.status_code == 200
    assert response.text == "challenge_code_987654"


def test_meta_webhook_verification_wrong_token():
    """Test xác thực Webhook bị từ chối 403 khi sai verify_token."""
    response = client.get(
        "/api/v1/meta/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "invalid_wrong_token",
            "hub.challenge": "challenge_code_987654",
        },
    )
    assert response.status_code == 403
    assert "Verification token mismatch" in response.json()["detail"]


def test_meta_webhook_receive_message_event():
    """Test tiếp nhận sự kiện tin nhắn từ Facebook Messenger và trả về 200 OK ngay lập tức."""
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "1000888999",
                "time": 1729000000,
                "messaging": [
                    {
                        "sender": {"id": "user_psid_12345"},
                        "recipient": {"id": "1000888999"},
                        "timestamp": 1729000000,
                        "message": {
                            "mid": "m_xyz123",
                            "text": "Hello shop",
                        },
                    }
                ],
            }
        ],
    }

    with patch("app.services.meta.meta_service.process_incoming_message") as mock_process:
        response = client.post("/api/v1/meta/webhook", json=payload)
        assert response.status_code == 200
        assert response.text == "EVENT_RECEIVED"
        mock_process.assert_called_once_with("user_psid_12345", "Hello shop")


def test_meta_webhook_ignore_echo_message():
    """Test bỏ qua các tin nhắn echo do chính Fanpage gửi đi."""
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "1000888999",
                "messaging": [
                    {
                        "sender": {"id": "1000888999"},
                        "message": {
                            "mid": "m_xyz123",
                            "text": "Tin nhắn từ bot",
                            "is_echo": True,
                        },
                    }
                ],
            }
        ],
    }

    with patch("app.services.meta.meta_service.process_incoming_message") as mock_process:
        response = client.post("/api/v1/meta/webhook", json=payload)
        assert response.status_code == 200
        mock_process.assert_not_called()
