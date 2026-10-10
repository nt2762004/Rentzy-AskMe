from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.models.document import Document, DocumentChunk
from app.schemas.knowledge import DocumentCreate, DocumentUpdate
from app.services.chunker import text_chunker
from app.services.embedder import embedding_service
from app.db.qdrant import get_qdrant_client
from app.core.config import settings
from typing import List, Dict, Any, Optional
import uuid

class IngestionService:
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        self._client = qdrant_client

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = get_qdrant_client()
        return self._client

    def ingest_document(self, db: Session, doc_create: DocumentCreate) -> Document:
        """Nạp tài liệu mới kèm kiểm tra Idempotent (ghi đè nếu trùng record_id)."""
        # 0. Kiểm tra nếu record_id đã tồn tại -> Ghi đè (Xóa bản ghi cũ cả Postgres & Qdrant)
        if doc_create.metadata.record_id:
            existing_doc = db.query(Document).filter(Document.record_id == doc_create.metadata.record_id).first()
            if existing_doc:
                self.delete_document(db, existing_doc.id)

        # 1. Tạo Document ID & lưu Postgres
        doc_id = str(uuid.uuid4())
        db_doc = Document(
            id=doc_id,
            title=doc_create.title,
            content=doc_create.content,
            record_id=doc_create.metadata.record_id,
            topic=doc_create.metadata.topic,
            sub_topic=doc_create.metadata.sub_topic,
            question=doc_create.metadata.question,
            answer=doc_create.metadata.answer,
            source_url=doc_create.metadata.source_url,
            updated_at=doc_create.metadata.updated_at,
            approver=doc_create.metadata.approver,
            version=doc_create.metadata.version,
            status=doc_create.metadata.status
        )
        db.add(db_doc)

        # 2. Tạo chunks
        chunks = text_chunker.chunk_document(doc_id=doc_id, doc=doc_create)
        
        qdrant_points = []
        for chk in chunks:
            # 3. Ghi DocumentChunk vào Postgres
            db_chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                chunk_index=chk["chunk_index"],
                content=chk["content"],
                qdrant_point_id=chk["point_id"]
            )
            db.add(db_chunk)

            # 4. Generate vector
            vector = embedding_service.generate_embedding(chk["content"])

            # 5. Payload cho Qdrant (Lưu toàn bộ Metadata & Tách riêng Question / Answer)
            payload = {
                "document_id": doc_id,
                "chunk_index": chk["chunk_index"],
                "content": chk["content"],
                "record_id": chk["metadata"].record_id,
                "sub_topic": chk["metadata"].sub_topic,
                "question": chk["metadata"].question,
                "answer": chk["metadata"].answer,
                "status": chk["metadata"].status,
                "topic": chk["metadata"].topic,
                "source_url": chk["metadata"].source_url,
                "updated_at": chk["metadata"].updated_at,
                "approver": chk["metadata"].approver,
                "version": chk["metadata"].version
            }

            qdrant_points.append(models.PointStruct(
                id=chk["point_id"],
                vector=vector,
                payload=payload
            ))

        db.commit()
        db.refresh(db_doc)

        # 6. Push to Qdrant Cloud
        if qdrant_points:
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=qdrant_points
            )

        return db_doc

    def update_document_status(self, db: Session, doc_id: str, new_status: str) -> Optional[Document]:
        """
        Cập nhật trạng thái (active / inactive) trong PostgreSQL 
        và đồng bộ Payload `status` cho tất cả vector points thuộc document trong Qdrant.
        """
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        if not db_doc:
            return None

        db_doc.status = new_status
        db.commit()
        db.refresh(db_doc)

        # Tìm danh sách qdrant_point_id của document
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        point_ids = [c.qdrant_point_id for c in chunks]

        if point_ids:
            self.client.set_payload(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                payload={"status": new_status},
                points=point_ids
            )

        return db_doc

    def delete_document(self, db: Session, doc_id: str) -> bool:
        """
        Xóa tài liệu khỏi PostgreSQL và xóa sạch các vector points liên quan khỏi Qdrant.
        """
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        if not db_doc:
            return False

        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
        point_ids = [c.qdrant_point_id for c in chunks]

        db.delete(db_doc)
        db.commit()

        if point_ids:
            self.client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=models.PointIdsList(points=point_ids)
            )

        return True

ingestion_service = IngestionService()
