import json
import logging
from typing import Optional, Dict, Any
from redis import Redis
from datetime import datetime
from app.core.config import settings
from app.schemas.chat import SessionState, ChatMessage

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self._redis_client: Optional[Redis] = None
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._init_redis()

    def _init_redis(self):
        try:
            if settings.REDIS_HOST:
                client = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD or None,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_timeout=5
                )
            elif settings.REDIS_URL:
                client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=5)
            else:
                client = Redis(host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=2)
            client.ping()
            self._redis_client = client
            logger.info("Kết nối Redis Session Store thành công!")
        except Exception as e:
            logger.warning(f"Không thể kết nối Redis ({e}). Tự động fallback sang In-Memory Session Store!")
            self._redis_client = None

    def _get_redis_key(self, session_id: str) -> str:
        """Tạo Key cấu trúc chuẩn hóa namespace cho Redis Insight (Folder: rentzy -> session -> session_id)."""
        return f"rentzy:session:{session_id}"

    def get_session(self, session_id: str) -> SessionState:
        """Lấy thông tin SessionState từ Redis Hash (hoặc Memory Fallback)."""
        key = self._get_redis_key(session_id)

        if self._redis_client:
            try:
                # 1. Đọc dữ liệu dạng Redis Hash
                hash_data = self._redis_client.hgetall(key)
                if hash_data:
                    messages_raw = json.loads(hash_data.get("messages", "[]"))
                    messages = [ChatMessage(**m) for m in messages_raw]
                    return SessionState(
                        session_id=session_id,
                        messages=messages,
                        fallback_count=int(hash_data.get("fallback_count", 0)),
                        current_intent=hash_data.get("current_intent") or None,
                        created_at=hash_data.get("created_at", datetime.now().isoformat()),
                        updated_at=hash_data.get("updated_at", datetime.now().isoformat())
                    )

                # 2. Fallback đọc key cũ (session:{session_id}) nếu có dữ liệu legacy
                legacy_key = f"session:{session_id}"
                legacy_str = self._redis_client.get(legacy_key)
                if legacy_str:
                    data_dict = json.loads(legacy_str)
                    session = SessionState(**data_dict)
                    # Migrate sang Hash mới
                    self.save_session(session)
                    self._redis_client.delete(legacy_key)
                    return session

            except Exception as e:
                logger.warning(f"Lỗi đọc Redis session ({e}), chuyển sang memory store")

        # Memory store fallback
        mem_data = self._memory_store.get(key)
        if mem_data:
            return SessionState(**mem_data)

        # Chưa có session -> Tạo mới
        return SessionState(session_id=session_id)

    def save_session(self, session: SessionState, ttl_seconds: Optional[int] = None) -> None:
        """Lưu SessionState dưới dạng cấu trúc HASH có định dạng đẹp mắt trong Redis Insight."""
        key = self._get_redis_key(session_id=session.session_id)
        session.updated_at = datetime.now().isoformat()
        ttl = ttl_seconds if ttl_seconds is not None else settings.REDIS_TTL

        # Chuyển tin nhắn sang danh sách Dict & Format JSON có lùi lề (indent=2) giúp xem trực quan trong Redis GUI
        messages_dicts = [m.model_dump() for m in session.messages]
        messages_pretty_json = json.dumps(messages_dicts, ensure_ascii=False, indent=2)

        mapping = {
            "session_id": session.session_id,
            "fallback_count": str(session.fallback_count),
            "current_intent": session.current_intent or "",
            "created_at": str(session.created_at),
            "updated_at": str(session.updated_at),
            "messages": messages_pretty_json
        }

        if self._redis_client:
            try:
                self._redis_client.hset(key, mapping=mapping)
                self._redis_client.expire(key, ttl)
            except Exception as e:
                logger.warning(f"Lỗi ghi Redis Hash session ({e}), ghi tạm vào memory store")
                self._memory_store[key] = session.model_dump()
        else:
            self._memory_store[key] = session.model_dump()

    def add_message(self, session_id: str, role: str, content: str, intent: Optional[str] = None) -> SessionState:
        """Thêm tin nhắn mới vào Chat History của phiên và cập nhật current_intent nếu có."""
        session = self.get_session(session_id)
        session.messages.append(ChatMessage(role=role, content=content))
        if intent:
            session.current_intent = intent
        self.save_session(session)
        return session

    def reset_fallback_count(self, session_id: str) -> SessionState:
        """Đặt lại biến đếm số lần thất bại (Fallback count = 0)."""
        session = self.get_session(session_id)
        session.fallback_count = 0
        self.save_session(session)
        return session

    def increment_fallback_count(self, session_id: str) -> int:
        """Tăng biến đếm số lần thất bại liên tiếp và trả về số lượng hiện tại."""
        session = self.get_session(session_id)
        session.fallback_count += 1
        self.save_session(session)
        return session.fallback_count

session_service = SessionService()
