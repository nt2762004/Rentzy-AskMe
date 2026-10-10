from typing import List, Dict, Any
from app.schemas.knowledge import DocumentCreate, ChunkMetadata
import uuid

class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc_id: str, doc: DocumentCreate) -> List[Dict[str, Any]]:
        """
        Chia một Document thành danh sách các Chunks 
        kèm theo ChunkMetadata (bao gồm document_id, chunk_index, status, topic, approver, version, source_url).
        """
        text = doc.content
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunk_meta = ChunkMetadata(
                        document_id=doc_id,
                        chunk_index=chunk_idx,
                        record_id=doc.metadata.record_id,
                        sub_topic=doc.metadata.sub_topic,
                        question=doc.metadata.question,
                        answer=doc.metadata.answer,
                        status=doc.metadata.status,
                        topic=doc.metadata.topic,
                        source_url=doc.metadata.source_url,
                        updated_at=doc.metadata.updated_at,
                        approver=doc.metadata.approver,
                        version=doc.metadata.version
                    )
                    chunks.append({
                        "point_id": str(uuid.uuid4()),
                        "chunk_index": chunk_idx,
                        "content": current_chunk,
                        "metadata": chunk_meta
                    })
                    chunk_idx += 1
                current_chunk = para

        if current_chunk:
            chunk_meta = ChunkMetadata(
                document_id=doc_id,
                chunk_index=chunk_idx,
                record_id=doc.metadata.record_id,
                sub_topic=doc.metadata.sub_topic,
                question=doc.metadata.question,
                answer=doc.metadata.answer,
                status=doc.metadata.status,
                topic=doc.metadata.topic,
                source_url=doc.metadata.source_url,
                updated_at=doc.metadata.updated_at,
                approver=doc.metadata.approver,
                version=doc.metadata.version
            )
            chunks.append({
                "point_id": str(uuid.uuid4()),
                "chunk_index": chunk_idx,
                "content": current_chunk,
                "metadata": chunk_meta
            })

        return chunks

text_chunker = TextChunker()
