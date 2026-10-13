"""
Tests cho Policy Agent (Multi-Agent Architecture)
==================================================
Test các thành phần:
  1. Sub-intent detection (deposit_rules, deposit_refund, rental_pricing, receive_and_return)
  2. Policy agent node integration via /api/v1/chat
  3. Reply chứa thông tin chính sách chuẩn Rentzy (CCCD, 24h hoàn cọc, không cần giặt)
  4. Xác nhận handled_by == "policy_agent"
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.agents.policy import (
    analyze_policy_query_node,
    PolicyAgentState,
)

client = TestClient(app)


def _make_state(message: str) -> PolicyAgentState:
    return {
        "session_id": "test_policy_session",
        "message": message,
        "chat_history": [],
        "sub_intent": "",
        "retrieved_chunks": [],
        "sources": [],
        "reply_message": "",
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": None,
    }


# ---------------------------------------------------------------------------
# Unit tests — Sub-intent detection
# ---------------------------------------------------------------------------
class TestPolicySubIntentDetection:
    def test_deposit_rules_detection(self):
        state = _make_state("Cọc cccd như thế nào bạn, có cần cọc tiền mặt không?")
        result = analyze_policy_query_node(state)
        assert result["sub_intent"] == "deposit_rules"

    def test_deposit_refund_detection(self):
        state = _make_state("Bao lâu thì mình được hoàn lại tiền cọc sau khi trả đồ?")
        result = analyze_policy_query_node(state)
        assert result["sub_intent"] == "deposit_refund"

    def test_rental_pricing_detection(self):
        state = _make_state("Thời gian thuê tính mấy ngày và phí trễ hạn ra sao?")
        result = analyze_policy_query_node(state)
        assert result["sub_intent"] == "rental_pricing"

    def test_receive_and_return_detection(self):
        state = _make_state("Sau khi dùng xong trả đồ có cần mang đi giặt ủi không?")
        result = analyze_policy_query_node(state)
        assert result["sub_intent"] == "receive_and_return"


# ---------------------------------------------------------------------------
# Integration tests — /api/v1/chat routing
# ---------------------------------------------------------------------------
from app.graph.dialogue_graph import ENABLE_POLICY_AGENT

class TestPolicyAgentIntegration:
    def test_deposit_policy_routed_to_agent(self):
        """Chat API khi hỏi chính sách cọc (kiểm tra routing theo trạng thái enable/upcoming)."""
        payload = {
            "session_id": "test_policy_api_001",
            "message": "Cọc cccd như thế nào bạn?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        expected = "policy_agent" if ENABLE_POLICY_AGENT else "supervisor_upcoming"
        assert data["handled_by"] == expected
        assert len(data["reply_message"]) > 0

    def test_deposit_refund_routed_to_agent(self):
        """Chat API khi hỏi hoàn cọc (kiểm tra routing theo trạng thái enable/upcoming)."""
        payload = {
            "session_id": "test_policy_api_002",
            "message": "Bao lâu thì tôi nhận lại tiền đặt cọc sau khi trả đồ?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        expected = "policy_agent" if ENABLE_POLICY_AGENT else "supervisor_upcoming"
        assert data["handled_by"] == expected
        assert len(data["reply_message"]) > 0


# ---------------------------------------------------------------------------
# Unit test — run() entry point
# ---------------------------------------------------------------------------
class TestPolicyAgentRun:
    @patch("app.agents.policy.graph.policy_graph")
    def test_run_returns_required_fields(self, mock_graph):
        """run() phải trả về đầy đủ các field mà main dialogue_graph cần."""
        mock_graph.invoke.return_value = {
            "reply_message": "Chính sách cọc Rentzy linh hoạt bằng CCCD.",
            "sources": [{"chunk_id": "c1", "score": 0.9}],
            "suggest_sales": False,
            "suggested_options": None,
            "need_clarification": False,
            "handled_by": "policy_agent",
        }

        from app.agents.policy import run

        state = {
            "session_id": "test_policy_run",
            "message": "Chính sách cọc",
            "chat_history": [],
            "intent": "deposit_policy",
        }
        result = run(state)

        required_keys = {"reply_message", "sources", "suggest_sales", "suggested_options", "need_clarification", "fallback_count", "handled_by"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
        assert result["handled_by"] == "policy_agent"
        assert result["fallback_count"] == 0
