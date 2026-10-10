import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==========================================
# CATEGORY 1: HEALTH CHECK & INFRASTRUCTURE
# ==========================================

def test_health_endpoint():
    """Kiểm thử trạng thái API Health Check."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["python_version"] == "3.12"

def test_list_documents_endpoint():
    """Kiểm thử API liệt kê tài liệu trong PostgreSQL."""
    response = client.get("/api/v1/knowledge/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# ==========================================
# CATEGORY 2: INGESTION & DOCUMENT CREATION
# ==========================================

def test_manual_ingest_document():
    """Kiểm thử nạp tài liệu thủ công kèm đầy đủ Metadata."""
    doc_payload = {
        "title": "Chính sách thử đồ tại Showroom 2026",
        "content": "Khách hàng được thử tối đa 3 mẫu sản phẩm tại showroom 51 đường số 41 Khánh Hội.",
        "metadata": {
            "status": "active",
            "topic": "showroom_fitting_policy",
            "source_url": "https://rentzy.vn/showroom-fitting",
            "updated_at": "2026-10-02",
            "approver": "Business Lead",
            "version": "1.0"
        }
    }
    response = client.post("/api/v1/knowledge/ingest", json=doc_payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == doc_payload["title"]
    assert data["metadata"]["topic"] == "showroom_fitting_policy"

    # Cleanup test document
    doc_id = data["id"]
    client.delete(f"/api/v1/knowledge/documents/{doc_id}")


# ==========================================
# CATEGORY 3: MULTI-METADATA & TOPIC FILTERING
# ==========================================

def test_search_by_topic_filtering():
    """Kiểm thử bộ lọc chính xác 100% theo Topic trong Qdrant Payload."""
    payload = {
        "query": "Giới thiệu dịch vụ Rentzy",
        "top_k": 3,
        "filter": {
            "status": "active",
            "topic": "rentzy_overview"
        }
    }
    response = client.post("/api/v1/knowledge/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Tất cả kết quả trả về phải thuộc topic rentzy_overview
    for item in data.get("results", []):
        assert item["metadata"]["topic"] == "rentzy_overview"

def test_multi_field_metadata_filter():
    """Kiểm thử kết hợp lọc đồng thời nhiều trường Metadata."""
    payload = {
        "query": "Chính sách thử đồ",
        "top_k": 3,
        "filter": {
            "status": "active",
            "approver": "Rentzy Business Team",
            "version": "1.0"
        }
    }
    response = client.post("/api/v1/knowledge/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    for item in data.get("results", []):
        assert item["metadata"]["status"] == "active"
        assert item["metadata"]["approver"] == "Rentzy Business Team"

def test_search_by_record_id_and_question_answer_fields():
    """Kiểm thử nạp bài kèm record_id/sub_topic/question/answer và lọc chính xác theo record_id."""
    doc_payload = {
        "title": "Chính sách hủy cọc đổi mẫu",
        "content": "Câu hỏi: Tôi được đổi mẫu không?\nTrả lời: Được đổi trước 3 ngày.",
        "metadata": {
            "record_id": "ASKME-999",
            "sub_topic": "test_sub_topic",
            "question": "Tôi được đổi mẫu không?",
            "answer": "Được đổi trước 3 ngày.",
            "status": "active",
            "topic": "deposit_policy",
            "source_url": "https://rentzy.vn/test",
            "updated_at": "2026-10-02",
            "approver": "Rentzy QA",
            "version": "1.0"
        }
    }
    ingest_res = client.post("/api/v1/knowledge/ingest", json=doc_payload)
    assert ingest_res.status_code == 200
    doc_id = ingest_res.json()["id"]

    # Search by record_id filter
    search_payload = {
        "query": "hủy cọc đổi mẫu",
        "top_k": 1,
        "filter": {
            "status": "active",
            "record_id": "ASKME-999"
        }
    }
    s_res = client.post("/api/v1/knowledge/search", json=search_payload)
    assert s_res.status_code == 200
    data = s_res.json()
    assert data["total_results"] > 0
    top_item = data["results"][0]
    assert top_item["metadata"]["record_id"] == "ASKME-999"
    assert top_item["question"] == "Tôi được đổi mẫu không?"
    assert top_item["answer"] == "Được đổi trước 3 ngày."

    # Cleanup
    client.delete(f"/api/v1/knowledge/documents/{doc_id}")


# ==========================================
# CATEGORY 4: ACTIVE / INACTIVE LIFECYCLE GUARDRAIL
# ==========================================

def test_active_inactive_guardrail_lifecycle():
    """
    Kiểm thử quy trình vô hiệu hóa bài viết:
    1. Nạp bài mới (active) -> Tìm kiếm thấy bài.
    2. Đổi status sang inactive -> Bài viết LẬP TỨC BIẾN MẤT khỏi kết quả tìm kiếm.
    3. Bật lại active -> Bài viết LẬP TỨC XUẤT HIỆN trở lại.
    """
    # Step 1: Ingest active doc
    unique_text = "Mã giảm giá đặc biệt RENTZY2026 tặng 50k cho đơn đầu tiên"
    doc_payload = {
        "title": "Chương trình khuyến mãi RENTZY2026",
        "content": f"Chi tiết: {unique_text}",
        "metadata": {
            "status": "active",
            "topic": "promotion_code",
            "source_url": "https://rentzy.vn/promo",
            "updated_at": "2026-10-02",
            "approver": "Marketing Lead",
            "version": "1.0"
        }
    }
    ingest_res = client.post("/api/v1/knowledge/ingest", json=doc_payload)
    assert ingest_res.status_code == 200
    doc_id = ingest_res.json()["id"]

    # Search step 1: Must find active doc
    search_payload = {
        "query": "Mã giảm giá RENTZY2026",
        "top_k": 3,
        "filter": {"status": "active"}
    }
    s1 = client.post("/api/v1/knowledge/search", json=search_payload).json()
    found_in_s1 = any(doc_id == item["metadata"]["document_id"] for item in s1.get("results", []))
    assert found_in_s1 is True, "Bài viết active phải xuất hiện trong tìm kiếm"

    # Step 2: Toggle to inactive
    update_res = client.put(f"/api/v1/knowledge/documents/{doc_id}/status?new_status=inactive")
    assert update_res.status_code == 200

    # Search step 2: Must NOT find inactive doc
    s2 = client.post("/api/v1/knowledge/search", json=search_payload).json()
    found_in_s2 = any(doc_id == item["metadata"]["document_id"] for item in s2.get("results", []))
    assert found_in_s2 is False, "Bài viết inactive tuyệt đối không được xuất hiện trong tìm kiếm active"

    # Step 3: Re-activate
    client.put(f"/api/v1/knowledge/documents/{doc_id}/status?new_status=active")
    s3 = client.post("/api/v1/knowledge/search", json=search_payload).json()
    found_in_s3 = any(doc_id == item["metadata"]["document_id"] for item in s3.get("results", []))
    assert found_in_s3 is True, "Bài viết sau khi bật lại active phải xuất hiện trở lại"

    # Cleanup
    client.delete(f"/api/v1/knowledge/documents/{doc_id}")

# ==========================================
# CATEGORY 5: SEMANTIC SEARCH ACCURACY & TOP_K
# ==========================================

def test_semantic_search_accuracy():
    """Kiểm thử độ tương đồng ngữ nghĩa khi dùng diễn đạt tự nhiên."""
    payload = {
        "query": "Tôi được thử bao nhiêu trang phục tại tiệm?",
        "top_k": 3,
        "filter": {"status": "active"}
    }
    response = client.post("/api/v1/knowledge/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    # Top result phải có score > 0.50
    top_score = data["results"][0]["score"]
    assert top_score >= 0.50

def test_top_k_parameter_limit():
    """Kiểm thử tham số top_k giới hạn chính xác số lượng kết quả."""
    for k in [1, 3, 5]:
        payload = {"query": "Thuê xe hay thử đồ", "top_k": k, "filter": {"status": "active"}}
        res = client.post("/api/v1/knowledge/search", json=payload).json()
        assert len(res["results"]) <= k

# ==========================================
# CATEGORY 6: DOCUMENT DELETION SYNC & EDGE CASES
# ==========================================

def test_document_deletion_sync():
    """Kiểm thử xóa tài liệu đồng bộ trên cả PostgreSQL và Qdrant Cloud."""
    doc_payload = {
        "title": "Tài liệu tạm thời cần xóa",
        "content": "Nội dung này sẽ bị xóa khỏi hệ thống tức thì.",
        "metadata": {
            "status": "active",
            "topic": "temp_to_delete",
            "source_url": "https://rentzy.vn/temp",
            "updated_at": "2026-10-02",
            "approver": "QA Lead",
            "version": "1.0"
        }
    }
    ingest_res = client.post("/api/v1/knowledge/ingest", json=doc_payload)
    doc_id = ingest_res.json()["id"]

    # Xóa document
    del_res = client.delete(f"/api/v1/knowledge/documents/{doc_id}")
    assert del_res.status_code == 200

    # Tìm kiếm lại -> Không còn dữ liệu
    search_payload = {
        "query": "Tài liệu tạm thời cần xóa",
        "top_k": 3,
        "filter": {"status": "active", "topic": "temp_to_delete"}
    }
    s_res = client.post("/api/v1/knowledge/search", json=search_payload).json()
    found = any(doc_id == item["metadata"]["document_id"] for item in s_res.get("results", []))
    assert found is False

def test_404_on_invalid_document_operations():
    """Kiểm thử xử lý lỗi khi thao tác trên document_id không tồn tại."""
    fake_id = "non-existent-uuid-9999"
    
    # 404 update status
    update_res = client.put(f"/api/v1/knowledge/documents/{fake_id}/status?new_status=inactive")
    assert update_res.status_code == 404

    # 404 delete
    del_res = client.delete(f"/api/v1/knowledge/documents/{fake_id}")
    assert del_res.status_code == 404
