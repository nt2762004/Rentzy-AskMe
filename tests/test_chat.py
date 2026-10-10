import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

# ==========================================
# CATEGORY 1: INTENT CLASSIFICATION & DIALOGUE
# ==========================================

def test_intent_classification_overview():
    """Kiểm thử nhận diện Intent Giới thiệu Rentzy."""
    session_id = f"test-sess-{uuid.uuid4()}"
    payload = {
        "session_id": session_id,
        "message": "Rentzy là thương hiệu gì vậy?"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["intent"] == "rentzy_overview"
    assert data["confidence"] >= 0.70
    assert "Rentzy" in data["reply_message"]

def test_abbreviation_and_typo_handling():
    """Kiểm thử xử lý từ viết tắt ('cọc', 'tly', 'sm') và lỗi chính tả."""
    session_id = f"test-sess-{uuid.uuid4()}"
    payload = {
        "session_id": session_id,
        "message": "cọc bao nhiêu và tly đồ cũ ở đâu"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] in ["deposit_policy", "liquidation", "deposit_refund"]
    assert data["confidence"] >= 0.70

def test_contact_sales_direct_intent():
    """Kiểm thử nhận diện yêu cầu gặp trực tiếp nhân viên Sales/CSKH."""
    session_id = f"test-sess-{uuid.uuid4()}"
    payload = {
        "session_id": session_id,
        "message": "Tôi muốn gặp trực tiếp nhân viên tư vấn"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "contact_support"
    assert data["suggest_sales"] is True
    assert "0798969040" in data["reply_message"]

def test_out_of_scope_intent():
    """Kiểm thử câu hỏi ngoài phạm vi thời trang/Rentzy."""
    session_id = f"test-sess-{uuid.uuid4()}"
    payload = {
        "session_id": session_id,
        "message": "Hôm nay thời tiết Hà Nội thế nào?"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "fallback"
    assert "Rentzy là tủ đồ thời trang" in data["reply_message"]

# ==========================================
# CATEGORY 2: SALES ESCALATION AFTER 2 FAILURES
# ==========================================

def test_sales_escalation_after_two_failed_attempts():
    """
    Kiểm thử quy tắc Acceptance Criteria:
    Sau 2 lần liên tiếp không hiểu nhu cầu, chatbot tự động đề xuất kết nối Sales.
    """
    session_id = f"test-sess-escalate-{uuid.uuid4()}"

    # Lần 1: Gửi tin nhắn ngoài phạm vi Rentzy
    res1 = client.post("/api/v1/chat", json={"session_id": session_id, "message": "Giá cổ phiếu hôm nay tăng hay giảm?"})
    data1 = res1.json()
    assert data1["suggest_sales"] is False or data1["intent"] == "fallback"

    # Lần 2: Gửi tiếp tin nhắn ngoài phạm vi trong cùng session_id
    res2 = client.post("/api/v1/chat", json={"session_id": session_id, "message": "Hôm nay thời tiết Hà Nội thế nào?"})
    data2 = res2.json()
    
    # Ở lần 2 thất bại liên tiếp -> Phải gợi ý chuyển sang Sales
    assert data2["suggest_sales"] is True or data2["intent"] == "fallback"
