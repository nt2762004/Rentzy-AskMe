"""
Tests cho Membership Agent (Multi-Agent Architecture)
====================================================
Test các thành phần:
  1. Sub-intent detection (rule-based)
  2. Membership agent node integration via /api/v1/chat
  3. Reply luôn chứa link https://rentzy.vn/member-ship/
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.agents.membership import (
    analyze_membership_query_node,
    MembershipAgentState,
    MEMBERSHIP_REGISTER_URL,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_state(message: str) -> MembershipAgentState:
    return {
        "session_id": "test_membership_session",
        "message": message,
        "chat_history": [],
        "sub_intent": "",
        "retrieved_chunks": [],
        "sources": [],
        "reply_message": "",
        "suggest_sales": False,
        "suggested_options": None,
        "need_clarification": False,
    }


# ---------------------------------------------------------------------------
# Unit tests — Sub-intent detection
# ---------------------------------------------------------------------------
class TestSubIntentDetection:
    def test_overview_default(self):
        state = _make_state("Rentzy có các gói thành viên nào?")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "overview"

    def test_pricing_detection(self):
        state = _make_state("Gói Gold giá bao nhiêu tiền?")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "pricing"

    def test_benefits_detection(self):
        state = _make_state("Quyền lợi của gói VIP là gì?")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "benefits"

    def test_register_detection(self):
        state = _make_state("Tôi muốn đăng ký gói thành viên")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "register"

    def test_compare_detection(self):
        state = _make_state("So sánh gói Silver và Gold cho tôi")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "compare"

    def test_renew_detection(self):
        state = _make_state("Làm sao để gia hạn gói thành viên?")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "renew"

    def test_upgrade_detection(self):
        state = _make_state("Tôi muốn nâng cấp từ Silver lên Gold")
        result = analyze_membership_query_node(state)
        assert result["sub_intent"] == "renew"


# ---------------------------------------------------------------------------
# Integration tests — /api/v1/chat routes to membership_agent
# ---------------------------------------------------------------------------
class TestMembershipAgentIntegration:
    def test_membership_intent_routed_to_agent(self):
        """Chat API phải nhận diện intent=membership và trả về reply."""
        payload = {
            "session_id": "test_membership_api_001",
            "message": "Các gói Membership thành viên tại Rentzy gồm những gì?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["intent"] == "membership"
        assert data["handled_by"] == "membership_agent"
        assert len(data["reply_message"]) > 0

    def test_membership_reply_always_contains_link(self):
        """Reply phải luôn chứa link https://rentzy.vn/member-ship/."""
        payload = {
            "session_id": "test_membership_api_002",
            "message": "Gói thành viên Rentzy có những ưu đãi gì?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert MEMBERSHIP_REGISTER_URL in data["reply_message"], (
            f"Link {MEMBERSHIP_REGISTER_URL} phải có trong reply_message"
        )

    def test_membership_no_suggest_sales(self):
        """Membership agent không được kích hoạt suggest_sales."""
        payload = {
            "session_id": "test_membership_api_003",
            "message": "Cho tôi biết về gói Silver",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["intent"] == "membership"
        assert data["suggest_sales"] is False

    def test_membership_sources_returned(self):
        """Membership agent phải trả về sources từ Qdrant (hoặc list rỗng nếu không có data)."""
        payload = {
            "session_id": "test_membership_api_004",
            "message": "Quyền lợi gói VIP",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], (list, type(None)))


# ---------------------------------------------------------------------------
# Unit test — run() entry point returns correct fields
# ---------------------------------------------------------------------------
class TestMembershipAgentRun:
    @patch("app.agents.membership.graph.membership_graph")
    def test_run_returns_required_fields(self, mock_graph):
        """run() phải trả về đầy đủ các field mà main dialogue_graph cần."""
        mock_graph.invoke.return_value = {
            "reply_message": f"Đây là các gói thành viên...\n\n{MEMBERSHIP_REGISTER_URL}",
            "sources": [{"chunk_id": "abc", "score": 0.92}],
            "suggest_sales": False,
            "suggested_options": None,
            "need_clarification": False,
        }

        from app.agents.membership import run

        state = {
            "session_id": "test_run_001",
            "message": "Gói membership",
            "chat_history": [],
            "intent": "membership",
        }
        result = run(state)

        required_keys = {"reply_message", "sources", "suggest_sales", "suggested_options", "need_clarification", "fallback_count", "handled_by"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
        assert result["fallback_count"] == 0
        assert result["handled_by"] == "membership_agent"
        assert MEMBERSHIP_REGISTER_URL in result["reply_message"]
