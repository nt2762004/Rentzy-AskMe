"""
Tests cho Overview Agent (Multi-Agent Architecture)
===================================================
Test các thành phần:
  1. Sub-intent detection (rule-based)
  2. Overview agent node integration via /api/v1/chat
  3. Reply chứa thông tin Showroom / Hotline chuẩn Rentzy
  4. Xác nhận handled_by == "overview_agent"
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.agents.overview import (
    analyze_overview_query_node,
    OverviewAgentState,
    SHOWROOM_ADDRESS,
    HOTLINE_NUMBER,
)

client = TestClient(app)


def _make_state(message: str) -> OverviewAgentState:
    return {
        "session_id": "test_overview_session",
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
class TestOverviewSubIntentDetection:
    def test_showroom_detection(self):
        state = _make_state("Showroom Rentzy ở đâu vậy bạn?")
        result = analyze_overview_query_node(state)
        assert result["sub_intent"] == "showroom_address"

    def test_hotline_detection(self):
        state = _make_state("Cho mình số điện thoại hotline liên hệ")
        result = analyze_overview_query_node(state)
        assert result["sub_intent"] == "hotline_contact"

    def test_brand_intro_detection(self):
        state = _make_state("Rentzy là gì vậy?")
        result = analyze_overview_query_node(state)
        assert result["sub_intent"] == "brand_intro"

    def test_business_model_detection(self):
        state = _make_state("Mô hình thuê đồ của Rentzy hoạt động thế nào?")
        result = analyze_overview_query_node(state)
        assert result["sub_intent"] == "business_model"


# ---------------------------------------------------------------------------
# Integration tests — /api/v1/chat routes to overview_agent
# ---------------------------------------------------------------------------
class TestOverviewAgentIntegration:
    def test_overview_intent_routed_to_agent(self):
        """Chat API phải nhận diện intent=rentzy_overview và routed to overview_agent."""
        payload = {
            "session_id": "test_overview_api_001",
            "message": "Rentzy là gì, showroom ở đâu?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["intent"] == "rentzy_overview"
        assert data["handled_by"] == "overview_agent"
        assert len(data["reply_message"]) > 0

    def test_overview_reply_contains_contact_info(self):
        """Khi hỏi địa chỉ showroom, câu trả lời phải nhắc đến showroom hoặc hotline."""
        payload = {
            "session_id": "test_overview_api_002",
            "message": "Địa chỉ showroom Rentzy ở đâu?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["handled_by"] == "overview_agent"
        # Địa chỉ Khánh Hội hoặc Hotline
        assert "Khánh Hội" in data["reply_message"] or "41" in data["reply_message"] or HOTLINE_NUMBER in data["reply_message"]


# ---------------------------------------------------------------------------
# Unit test — run() entry point
# ---------------------------------------------------------------------------
class TestOverviewAgentRun:
    @patch("app.agents.overview.graph.overview_graph")
    def test_run_returns_required_fields(self, mock_graph):
        """run() phải trả về đầy đủ các field mà main dialogue_graph cần."""
        mock_graph.invoke.return_value = {
            "reply_message": f"Showroom Rentzy tại {SHOWROOM_ADDRESS}",
            "sources": [{"chunk_id": "chunk_1", "score": 0.95}],
            "suggest_sales": False,
            "suggested_options": None,
            "need_clarification": False,
            "handled_by": "overview_agent",
        }

        from app.agents.overview import run

        state = {
            "session_id": "test_overview_run",
            "message": "Địa chỉ showroom",
            "chat_history": [],
            "intent": "rentzy_overview",
        }
        result = run(state)

        required_keys = {"reply_message", "sources", "suggest_sales", "suggested_options", "need_clarification", "fallback_count", "handled_by"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
        assert result["handled_by"] == "overview_agent"
        assert result["fallback_count"] == 0
