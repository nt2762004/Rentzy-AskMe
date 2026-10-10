from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.services.embedder import embedding_service
from app.db.qdrant import get_qdrant_client
from app.schemas.knowledge import SearchRequest, SearchResponse, SearchResultItem, ChunkMetadata
from app.core.config import settings
from typing import List, Optional

class KnowledgeSearchService:
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        self._client = qdrant_client

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = get_qdrant_client()
        return self._client

    def search_knowledge(self, search_req: SearchRequest) -> SearchResponse:
        """
        Tìm kiếm ngữ nghĩa trên Qdrant Cloud 
        kết hợp bộ lọc Đa Metadata (status, topic, approver, version, source_url).
        """
        # 1. Tạo Query Embedding
        query_vector = embedding_service.generate_embedding(search_req.query)

        # 2. Dựng bộ lọc Multi-Metadata Qdrant Filter
        must_conditions = []
        filter_opts = search_req.filter

        if filter_opts:
            if filter_opts.status:
                must_conditions.append(models.FieldCondition(
                    key="status",
                    match=models.MatchValue(value=filter_opts.status)
                ))
            if filter_opts.record_id:
                must_conditions.append(models.FieldCondition(
                    key="record_id",
                    match=models.MatchValue(value=filter_opts.record_id)
                ))
            if filter_opts.topic:
                must_conditions.append(models.FieldCondition(
                    key="topic",
                    match=models.MatchValue(value=filter_opts.topic)
                ))
            if filter_opts.sub_topic:
                must_conditions.append(models.FieldCondition(
                    key="sub_topic",
                    match=models.MatchValue(value=filter_opts.sub_topic)
                ))
            if filter_opts.approver:
                must_conditions.append(models.FieldCondition(
                    key="approver",
                    match=models.MatchValue(value=filter_opts.approver)
                ))
            if filter_opts.version:
                must_conditions.append(models.FieldCondition(
                    key="version",
                    match=models.MatchValue(value=filter_opts.version)
                ))
            if filter_opts.source_url:
                must_conditions.append(models.FieldCondition(
                    key="source_url",
                    match=models.MatchValue(value=filter_opts.source_url)
                ))

        qdrant_filter = models.Filter(must=must_conditions) if must_conditions else None

        # 3. Thực hiện Vector Search bằng query_points
        search_response = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=search_req.top_k
        )
        search_results = search_response.points

        # 4. Chuẩn hóa kết quả trả về
        results_items = []
        for res in search_results:
            payload = res.payload or {}
            meta = ChunkMetadata(
                document_id=payload.get("document_id", ""),
                chunk_index=payload.get("chunk_index", 0),
                record_id=payload.get("record_id"),
                sub_topic=payload.get("sub_topic"),
                question=payload.get("question"),
                answer=payload.get("answer"),
                status=payload.get("status", "active"),
                topic=payload.get("topic", ""),
                source_url=payload.get("source_url", ""),
                updated_at=payload.get("updated_at", ""),
                approver=payload.get("approver", ""),
                version=payload.get("version", "1.0")
            )
            results_items.append(SearchResultItem(
                chunk_id=str(res.id),
                question=payload.get("question"),
                answer=payload.get("answer"),
                content=payload.get("content", ""),
                score=round(float(res.score), 4),
                metadata=meta
            ))

        return SearchResponse(
            query=search_req.query,
            total_results=len(results_items),
            results=results_items
        )

search_service = KnowledgeSearchService()
