"""
Tests cho Support Agent (Multi-Agent Architecture)
==================================================
Test các thành phần:
  1. Sub-intent detection (rule-based)
  2. Support agent node integration via /api/v1/chat
  3. Reply chứa Hotline 0798969040 và suggest_sales == True
  4. Xác nhận handled_by == "support_agent"
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.agents.support import (
    analyze_support_query_node,
    SupportAgentState,
    HOTLINE_NUMBER,
    SHOWROOM_ADDRESS,
)

client = TestClient(app)


def _make_state(message: str) -> SupportAgentState:
    return {
        "session_id": "test_support_session",
        "message": message,
        "chat_history": [],
        "sub_intent": "",
        "retrieved_chunks": [],
        "sources": [],
        "reply_message": "",
        "suggest_sales": True,
        "suggested_options": None,
        "need_clarification": False,
        "handled_by": None,
    }


# ---------------------------------------------------------------------------
# Unit tests — Sub-intent detection
# ---------------------------------------------------------------------------
class TestSupportSubIntentDetection:
    def test_hotline_call_detection(self):
        state = _make_state("Cho mình xin số điện thoại hotline cskh")
        result = analyze_support_query_node(state)
        assert result["sub_intent"] == "hotline_call"

    def test_human_agent_detection(self):
        state = _make_state("Mình muốn nói chuyện với người thật, gặp nhân viên tư vấn")
        result = analyze_support_query_node(state)
        assert result["sub_intent"] == "human_agent"

    def test_order_support_detection(self):
        state = _make_state("Kiểm tra mã đơn hàng và tình trạng đơn thuê của mình")
        result = analyze_support_query_node(state)
        assert result["sub_intent"] == "order_support"

    def test_complaint_detection(self):
        state = _make_state("Váy bị sự cố rách chỉ, mình muốn khiếu nại đổi gấp")
        result = analyze_support_query_node(state)
        assert result["sub_intent"] == "complaint"


# ---------------------------------------------------------------------------
# Integration tests — /api/v1/chat routes to support_agent
# ---------------------------------------------------------------------------
class TestSupportAgentIntegration:
    def test_contact_support_routed_to_agent(self):
        """Chat API phải nhận diện intent=contact_support và routed to support_agent."""
        payload = {
            "session_id": "test_support_api_001",
            "message": "Cho mình xin số hotline cskh",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["intent"] == "contact_support"
        assert data["handled_by"] == "support_agent"
        assert data["suggest_sales"] is True
        assert HOTLINE_NUMBER in data["reply_message"]

    def test_order_support_routed_to_agent(self):
        """Chat API khi hỏi tra cứu đơn hàng phải routed to support_agent."""
        payload = {
            "session_id": "test_support_api_002",
            "message": "Tra cứu mã đơn hàng của mình",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["handled_by"] == "support_agent"
        assert len(data["reply_message"]) > 0


# ---------------------------------------------------------------------------
# Unit test — run() entry point
# ---------------------------------------------------------------------------
class TestSupportAgentRun:
    @patch("app.agents.support.graph.support_graph")
    def test_run_returns_required_fields(self, mock_graph):
        """run() phải trả về đầy đủ các field mà main dialogue_graph cần."""
        mock_graph.invoke.return_value = {
            "reply_message": f"Hotline CSKH: {HOTLINE_NUMBER}",
            "sources": [],
            "suggest_sales": True,
            "suggested_options": None,
            "need_clarification": False,
            "handled_by": "support_agent",
        }

        from app.agents.support import run

        state = {
            "session_id": "test_support_run",
            "message": "Gặp tư vấn viên",
            "chat_history": [],
            "intent": "contact_support",
        }
        result = run(state)

        required_keys = {"reply_message", "sources", "suggest_sales", "suggested_options", "need_clarification", "fallback_count", "handled_by"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
        assert result["handled_by"] == "support_agent"
        assert result["suggest_sales"] is True
        assert result["fallback_count"] == 0
