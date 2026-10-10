from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.postgres import get_db
from app.models.document import Document
from app.schemas.knowledge import (
    DocumentCreate, DocumentResponse, DocumentMetadata,
    SearchRequest, SearchResponse
)
from app.services.extractor import excel_extractor
from app.services.ingestion import ingestion_service
from app.services.search import search_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.post("/seed-excel", summary="Nạp toàn bộ dữ liệu từ file Excel Rentzy vào Postgres & Qdrant Cloud")
def seed_excel_data(db: Session = Depends(get_db)):
    """Đọc dữ liệu từ docs/Rentzy_AskMe_AI_Training_Data.xlsx và nạp tự động vào hệ thống."""
    try:
        documents = excel_extractor.extract_documents()
        ingested_docs = []
        for doc in documents:
            db_doc = ingestion_service.ingest_document(db, doc)
            ingested_docs.append({
                "id": db_doc.id,
                "record_id": db_doc.record_id,
                "title": db_doc.title,
                "topic": db_doc.topic,
                "sub_topic": db_doc.sub_topic,
                "question": db_doc.question,
                "answer": db_doc.answer
            })
        return {
            "message": "Nạp dữ liệu Excel thành công!",
            "total_ingested": len(ingested_docs),
            "documents": ingested_docs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi nạp dữ liệu Excel: {str(e)}"
        )

@router.post("/ingest", summary="Nạp tài liệu mới thủ công", response_model=DocumentResponse)
def ingest_document(doc_create: DocumentCreate, db: Session = Depends(get_db)):
    """Nạp một bài viết/tài liệu mới kèm metadata đầy đủ."""
    db_doc = ingestion_service.ingest_document(db, doc_create)
    return DocumentResponse(
        id=db_doc.id,
        title=db_doc.title,
        metadata=DocumentMetadata(
            record_id=db_doc.record_id,
            sub_topic=db_doc.sub_topic,
            question=db_doc.question,
            answer=db_doc.answer,
            status=db_doc.status,
            topic=db_doc.topic,
            source_url=db_doc.source_url,
            updated_at=db_doc.updated_at,
            approver=db_doc.approver,
            version=db_doc.version
        ),
        created_at=db_doc.created_at,
        updated_at_dt=db_doc.updated_at_dt
    )

@router.post("/search", summary="Tìm kiếm ngữ nghĩa với bộ lọc Đa Metadata", response_model=SearchResponse)
def search_knowledge(search_req: SearchRequest):
    """
    Tìm kiếm thông tin trong Kho kiến thức.
    Bộ lọc mặc định chỉ trả về các chunk có status == 'active'.
    Có thể lọc kết hợp thêm: topic, sub_topic, record_id, approver, version, source_url.
    """
    return search_service.search_knowledge(search_req)

@router.put("/documents/{doc_id}/status", summary="Cập nhật trạng thái Active/Inactive của tài liệu")
def update_document_status(doc_id: str, new_status: str = Query(..., pattern="^(active|inactive)$"), db: Session = Depends(get_db)):
    """Cập nhật trạng thái tài liệu trong Postgres và đồng bộ tức thì trên Qdrant Cloud."""
    db_doc = ingestion_service.update_document_status(db, doc_id, new_status)
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu")
    return {
        "message": f"Đã cập nhật trạng thái tài liệu sang '{new_status}'",
        "document_id": doc_id,
        "new_status": new_status
    }

@router.get("/documents", summary="Danh sách tài liệu trong PostgreSQL")
def list_documents(
    topic: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Liệt kê danh sách tài liệu đang lưu trữ."""
    query = db.query(Document)
    if topic:
        query = query.filter(Document.topic == topic)
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    docs = query.order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "record_id": d.record_id,
            "topic": d.topic,
            "sub_topic": d.sub_topic,
            "question": d.question,
            "answer": d.answer,
            "source_url": d.source_url,
            "status": d.status,
            "version": d.version,
            "approver": d.approver,
            "updated_at": d.updated_at
        }
        for d in docs
    ]

@router.delete("/documents/{doc_id}", summary="Xóa tài liệu khỏi hệ thống")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Xóa hoàn toàn tài liệu khỏi Postgres và Qdrant Cloud."""
    success = ingestion_service.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu để xóa")
    return {"message": "Đã xóa tài liệu và các vector liên quan thành công!", "document_id": doc_id}
