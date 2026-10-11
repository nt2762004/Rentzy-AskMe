import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_index_page_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "RENTZY" in response.text
    assert "rentzy-widget.js" in response.text

def test_static_js_widget_file():
    response = client.get("/static/js/rentzy-widget.js")
    assert response.status_code == 200
    assert "RentzyWidgetInitialized" in response.text
    assert "rentzy_askme_session_id" in response.text
    assert "https://maps.app.goo.gl/ShHNabftWGUSmy6N6" in response.text
    assert "https://rentzy.vn/member-ship/" in response.text
    assert "Cần hỗ trợ không người đẹp" in response.text
    assert "https://zalo.me/3199663178050331455" in response.text

def test_static_css_widget_file():
    response = client.get("/static/css/rentzy-widget.css")
    assert response.status_code == 200
    assert "#rentzy-widget-root" in response.text or ".rw-chat-window" in response.text
    assert "--rw-rose" in response.text or "--rw-gold" in response.text

def test_widget_chat_api_integration():
    payload = {
        "session_id": "test_widget_session_123",
        "message": "Cho tôi biết thông tin tổng quan về dịch vụ Rentzy"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_widget_session_123"
    assert data["intent"] == "rentzy_overview"
    assert len(data["reply_message"]) > 0
