"""
Tests cho Catalog & Product Agent (Multi-Agent Architecture)
============================================================
Test các thành phần:
  1. Sub-intent detection (product_search, product_price, rent_vs_liquidation, liquidation_items)
  2. Catalog agent node integration via /api/v1/chat
  3. Reply chứa link bộ sưu tập hoặc showroom
  4. Xác nhận handled_by == "catalog_agent"
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.agents.catalog import (
    analyze_catalog_query_node,
    CatalogAgentState,
    COLLECTIONS_URL,
)

client = TestClient(app)


def _make_state(message: str) -> CatalogAgentState:
    return {
        "session_id": "test_catalog_session",
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
class TestCatalogSubIntentDetection:
    def test_rent_vs_liquidation_detection(self):
        state = _make_state("Dùng 1 lần đi tiệc thì nên thuê hay mua thanh lý?")
        result = analyze_catalog_query_node(state)
        assert result["sub_intent"] == "rent_vs_liquidation"

    def test_liquidation_items_detection(self):
        state = _make_state("Rentzy có bán đồ thanh lý không bạn, xem đầm thanh lý ở đâu?")
        result = analyze_catalog_query_node(state)
        assert result["sub_intent"] == "liquidation_items"

    def test_product_price_detection(self):
        state = _make_state("Giá thuê đầm dạ hội này khoảng bao nhiêu tiền?")
        result = analyze_catalog_query_node(state)
        assert result["sub_intent"] == "product_price"

    def test_product_search_detection(self):
        state = _make_state("Tìm cho mình mẫu váy đỏ dự tiệc cưới size M")
        result = analyze_catalog_query_node(state)
        assert result["sub_intent"] == "product_search"


# ---------------------------------------------------------------------------
# Integration tests — /api/v1/chat routing
# ---------------------------------------------------------------------------
from app.graph.dialogue_graph import ENABLE_CATALOG_AGENT

class TestCatalogAgentIntegration:
    def test_product_search_routed_to_agent(self):
        """Chat API khi tìm kiếm sản phẩm (kiểm tra routing theo trạng thái enable/upcoming)."""
        payload = {
            "session_id": "test_catalog_api_001",
            "message": "Tìm cho mình mẫu váy đỏ dự tiệc cưới size M",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        expected = "catalog_agent" if ENABLE_CATALOG_AGENT else "supervisor_upcoming"
        assert data["handled_by"] == expected
        assert len(data["reply_message"]) > 0

    def test_liquidation_routed_to_agent(self):
        """Chat API khi hỏi đồ thanh lý (kiểm tra routing theo trạng thái enable/upcoming)."""
        payload = {
            "session_id": "test_catalog_api_002",
            "message": "Xem đầm thanh lý ở đâu vậy bạn?",
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200

        data = response.json()
        expected = "catalog_agent" if ENABLE_CATALOG_AGENT else "supervisor_upcoming"
        assert data["handled_by"] == expected
        assert len(data["reply_message"]) > 0


# ---------------------------------------------------------------------------
# Unit test — run() entry point
# ---------------------------------------------------------------------------
class TestCatalogAgentRun:
    @patch("app.agents.catalog.graph.catalog_graph")
    def test_run_returns_required_fields(self, mock_graph):
        """run() phải trả về đầy đủ các field mà main dialogue_graph cần."""
        mock_graph.invoke.return_value = {
            "reply_message": f"Nàng có thể xem bộ sưu tập tại {COLLECTIONS_URL}",
            "sources": [{"chunk_id": "c1", "score": 0.9}],
            "suggest_sales": False,
            "suggested_options": None,
            "need_clarification": False,
            "handled_by": "catalog_agent",
        }

        from app.agents.catalog import run

        state = {
            "session_id": "test_catalog_run",
            "message": "Tìm váy dạ hội",
            "chat_history": [],
            "intent": "product_search",
        }
        result = run(state)

        required_keys = {"reply_message", "sources", "suggest_sales", "suggested_options", "need_clarification", "fallback_count", "handled_by"}
        assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
        assert result["handled_by"] == "catalog_agent"
        assert result["fallback_count"] == 0
