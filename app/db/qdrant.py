from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

def get_qdrant_client() -> QdrantClient:
    """Tạo client kết nối Qdrant với timeout 5.0s tránh treo app khi khởi động."""
    if settings.QDRANT_API_KEY:
        return QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=5.0)
    return QdrantClient(url=settings.QDRANT_URL, timeout=5.0)

def init_qdrant_collection(client: QdrantClient = None, force_recreate: bool = False) -> None:
    """
    Khởi tạo collection trong Qdrant và đánh Payload Index 
    cho tất cả các trường metadata (status, topic, approver, version, source_url).
    """
    try:
        if client is None:
            client = get_qdrant_client()

        collection_name = settings.QDRANT_COLLECTION_NAME

        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
    except Exception as exc:
        logger.warning(f"Không thể kết nối Qdrant khi khởi động ({exc}). Bỏ qua bước kiểm tra collection.")
        return

    need_recreate = force_recreate
    if collection_name in collection_names and not force_recreate:
        # Kiểm tra xem collection cũ có khớp dimension 384 không
        info = client.get_collection(collection_name)
        params = info.config.params
        if isinstance(params.vectors, dict):
            # Cũ là named vectors (như text_dense 1536) -> Cần recreate về unnamed vector 384
            need_recreate = True
        elif hasattr(params.vectors, 'size') and params.vectors.size != settings.EMBEDDING_DIMENSION:
            need_recreate = True

    if need_recreate and collection_name in collection_names:
        client.delete_collection(collection_name)
        collection_names.remove(collection_name)

    if collection_name not in collection_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE
            )
        )

    # Đánh chỉ mục Payload Index cho các trường Metadata quan trọng
    payload_fields = [
        ("status", models.PayloadSchemaType.KEYWORD),
        ("topic", models.PayloadSchemaType.KEYWORD),
        ("sub_topic", models.PayloadSchemaType.KEYWORD),
        ("record_id", models.PayloadSchemaType.KEYWORD),
        ("approver", models.PayloadSchemaType.KEYWORD),
        ("version", models.PayloadSchemaType.KEYWORD),
        ("source_url", models.PayloadSchemaType.KEYWORD),
        ("document_id", models.PayloadSchemaType.KEYWORD),
    ]

    for field_name, field_type in payload_fields:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=field_type
        )
