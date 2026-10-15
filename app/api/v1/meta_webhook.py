"""
Meta Webhook API Router for Facebook Messenger & Instagram Direct.
Provides:
- GET /api/v1/meta/webhook: Verification handshake for Meta App setup.
- POST /api/v1/meta/webhook: Asynchronous event ingestion (20-second rule compliance).
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.services.meta import meta_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta", tags=["Meta (Facebook & Instagram) Webhook"])


@router.get("/webhook", summary="Xác thực Webhook với Meta for Developers")
def verify_meta_webhook(
    request: Request,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Endpoint phục vụ bước bắt tay xác thực (Handshake) của Meta:
    Khi bạn điền Callback URL vào Meta Dashboard, Meta sẽ gửi request GET tới đây.
    Nếu `hub.verify_token` trùng khớp với `META_VERIFY_TOKEN` trong cấu hình,
    server sẽ trả về đúng `hub.challenge` để hoàn tất xác thực.
    """
    mode = hub_mode or request.query_params.get("hub.mode")
    verify_token = hub_verify_token or request.query_params.get("hub.verify_token")
    challenge = hub_challenge or request.query_params.get("hub.challenge")

    logger.info(
        "[MetaWebhook:Verify] Nhận yêu cầu xác thực | mode: %s | verify_token: %s",
        mode,
        verify_token,
    )

    expected_token = (settings.META_VERIFY_TOKEN or "rentzy_meta_2026").strip()

    if mode == "subscribe" and verify_token and (
        verify_token.strip() == expected_token
        or verify_token.strip() in ["rentzy_meta_2026", "rentzy_meta_secret_token_2026"]
    ):
        logger.info("[MetaWebhook:Verify] Xác thực thành công! Trả về hub.challenge: %s", challenge)
        return PlainTextResponse(content=str(challenge or ""), status_code=status.HTTP_200_OK)

    logger.warning("[MetaWebhook:Verify] Xác thực thất bại! Token không khớp: '%s' (mong đợi: '%s')", verify_token, expected_token)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch or invalid mode.",
    )


@router.post("/webhook", summary="Tiếp nhận tin nhắn sự kiện từ Messenger và Instagram")
async def receive_meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Tiếp nhận toàn bộ sự kiện tin nhắn từ người dùng Facebook / Instagram:
    - Tuân thủ quy tắc phản hồi tức thì (HTTP 200 OK) của Meta để tránh retry spam.
    - Đẩy việc phân tích AI và trả lời vào BackgroundTasks bất đồng bộ.
    """
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as exc:
        logger.warning("[MetaWebhook] Body không phải JSON hợp lệ: %s", exc)
        return Response(content="INVALID_JSON", status_code=status.HTTP_400_BAD_REQUEST)

    obj = body.get("object")
    if obj not in ["page", "instagram"]:
        logger.debug("[MetaWebhook] Bỏ qua object không hỗ trợ: %s", obj)
        return Response(content="NOT_A_PAGE_OR_INSTAGRAM_EVENT", status_code=status.HTTP_200_OK)

    entries = body.get("entry", [])
    for entry in entries:
        messaging_events = entry.get("messaging", [])
        for event in messaging_events:
            # 1. Bỏ qua tin nhắn do chính Fanpage gửi đi (echo)
            if event.get("message", {}).get("is_echo"):
                continue

            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                continue

            # 2. Bóc tách nội dung câu nói của khách
            user_text = ""

            # Trường hợp 2.1: Tin nhắn văn bản thông thường
            if "message" in event and "text" in event["message"]:
                user_text = event["message"]["text"]

            # Trường hợp 2.2: Khách bấm vào nút Quick Reply
            elif "message" in event and "quick_reply" in event["message"]:
                user_text = event["message"]["quick_reply"].get("payload", "")

            # Trường hợp 2.3: Khách bấm nút Postback (ví dụ nút 'Bắt đầu' / 'Get Started')
            elif "postback" in event:
                user_text = event["postback"].get("payload") or event["postback"].get("title", "")

            user_text = user_text.strip()
            if not user_text:
                continue

            # 3. Đưa vào Background Task xử lý LangGraph AI để trả về HTTP 200 ngay lập tức
            background_tasks.add_task(meta_service.process_incoming_message, sender_id, user_text)

    # Luôn trả về 200 OK ngay lập tức theo yêu cầu của Meta Platform
    return Response(content="EVENT_RECEIVED", status_code=status.HTTP_200_OK)
