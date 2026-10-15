"""
Meta Graph API Service for Facebook Messenger & Instagram Direct.
Handles sending messages, typing indicators, quick replies, and processing background events.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.session import session_service
from app.graph.dialogue_graph import dialogue_graph

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"


class MetaService:
    """Service xử lý gửi/nhận tin nhắn qua Meta Graph API (Messenger & Instagram)."""

    def __init__(self):
        self.api_version = settings.META_API_VERSION
        self.access_token = settings.META_PAGE_ACCESS_TOKEN

    @property
    def send_url(self) -> str:
        return f"{GRAPH_API_BASE}/{self.api_version}/me/messages"

    async def send_sender_action(self, recipient_id: str, action: str = "typing_on") -> bool:
        """
        Gửi trạng thái tới Meta (typing_on, mark_seen...) để người dùng thấy bot đang soạn tin.
        """
        if not self.access_token:
            return False

        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": action,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    self.send_url,
                    json=payload,
                    params={"access_token": self.access_token},
                )
                return res.status_code == 200
        except Exception as exc:
            logger.debug("[MetaService:Action] Gặp lỗi khi gửi action '%s': %s", action, exc)
            return False

    async def send_text_message(
        self,
        recipient_id: str,
        text: str,
        quick_replies: Optional[List[str]] = None,
    ) -> bool:
        """
        Gửi tin nhắn văn bản kèm Quick Replies (nút gợi ý nhanh) tới người dùng.
        Tự động chia nhỏ tin nhắn nếu vượt quá giới hạn 2000 ký tự của Facebook.
        """
        if not self.access_token:
            logger.warning(
                "[MetaService:Send] Chưa cấu hình META_PAGE_ACCESS_TOKEN. Không thể gửi tin tới PSID=%s",
                recipient_id,
            )
            return False

        # Facebook giới hạn tối đa 2000 ký tự cho mỗi bubble tin nhắn
        chunks = self._chunk_text(text, max_len=1900)

        for i, chunk in enumerate(chunks):
            is_last = (i == len(chunks) - 1)
            payload: Dict[str, Any] = {
                "recipient": {"id": recipient_id},
                "message": {"text": chunk},
                "messaging_type": "RESPONSE",
            }

            # Chỉ gắn quick replies vào bubble tin nhắn cuối cùng
            if is_last and quick_replies:
                qr_payloads = []
                for option in quick_replies[:11]:  # Meta cho tối đa 13 quick replies
                    title = option.strip()
                    if not title:
                        continue
                    # Meta giới hạn title của quick reply tối đa 20 ký tự
                    truncated_title = title if len(title) <= 20 else title[:17] + "..."
                    qr_payloads.append({
                        "content_type": "text",
                        "title": truncated_title,
                        "payload": title,
                    })
                if qr_payloads:
                    payload["message"]["quick_replies"] = qr_payloads

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(
                        self.send_url,
                        json=payload,
                        params={"access_token": self.access_token},
                    )
                    if res.status_code != 200:
                        logger.error(
                            "[MetaService:Send] Lỗi gửi tin tới Meta (HTTP %d): %s",
                            res.status_code,
                            res.text,
                        )
                        return False
            except Exception as exc:
                logger.error("[MetaService:Send] Exception khi gửi tin nhắn tới Meta: %s", exc)
                return False

        logger.info("  └── [MetaService:Outbound] Đã gửi thành công %d bubble tin tới PSID=%s", len(chunks), recipient_id)
        return True

    def process_incoming_message(self, sender_id: str, message_text: str):
        """
        Xử lý tin nhắn đến trong Background Task:
        - Đẩy tin nhắn vào Session Store (session_id = fb_{sender_id}).
        - Kích hoạt LangGraph Multi-Agent.
        - Gửi câu trả lời về cho khách qua Meta Send API.
        """
        import asyncio

        session_id = f"meta_{sender_id}"
        logger.info("\n" + "=" * 60)
        logger.info("[MetaService:Inbound] Nhận tin nhắn từ PSID: %s | Text: '%s'", sender_id, message_text)

        try:
            # 1. Bật typing indicator (đang soạn tin...)
            asyncio.run(self.send_sender_action(sender_id, "typing_on"))

            # 2. Ghi nhận tin nhắn người dùng vào session
            session_service.add_message(session_id, role="user", content=message_text)

            # 3. Kích hoạt LangGraph Multi-Agent
            state_input = {
                "session_id": session_id,
                "message": message_text,
            }
            graph_output = dialogue_graph.invoke(state_input)

            intent_code = graph_output.get("intent", "out_of_scope")
            reply = graph_output.get(
                "reply_message",
                "Dạ Rentzy xin chào Nàng! Rentzy có thể hỗ trợ gì cho Nàng hôm nay ạ?",
            )
            suggested_options = graph_output.get("suggested_options")
            handled_by = graph_output.get("handled_by", "supervisor")

            # 4. Ghi nhận tin nhắn bot vào session
            session_service.add_message(session_id, role="assistant", content=reply, intent=intent_code)

            logger.info(
                "[MetaService:Processed] Intent: [%s] | Handled By: [%s] | Options: %s",
                intent_code,
                handled_by,
                suggested_options,
            )

            # 5. Gửi câu trả lời về lại Meta Messenger / Instagram
            asyncio.run(self.send_text_message(sender_id, reply, quick_replies=suggested_options))

        except Exception as exc:
            logger.error("[MetaService] Lỗi khi xử lý tin nhắn Meta: %s", exc, exc_info=True)
            fallback_msg = "Dạ Rentzy hiện đang bận xử lý, Nàng vui lòng gửi lại tin nhắn sau giây lát nhé ạ!"
            try:
                asyncio.run(self.send_text_message(sender_id, fallback_msg))
            except Exception:
                pass

    @staticmethod
    def _chunk_text(text: str, max_len: int = 1900) -> List[str]:
        """Cắt văn bản dài thành các đoạn nhỏ hơn max_len nhưng giữ nguyên câu hoặc dòng."""
        if len(text) <= max_len:
            return [text]

        chunks = []
        lines = text.split("\n")
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_len:
                current_chunk += ("\n" if current_chunk else "") + line
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line

        if current_chunk:
            chunks.append(current_chunk)
        return chunks if chunks else [text]


meta_service = MetaService()
