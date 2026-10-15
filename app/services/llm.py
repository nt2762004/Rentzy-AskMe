"""
Unified LLM Service with automatic failover across 4 chosen Gemini models:
1. gemini-3.1-flash-lite (ưu tiên chính)
2. gemini-3.5-flash-lite (dự phòng tầng 1)
3. gemini-3.6-flash (dự phòng tầng 2)
4. gemini-3.8-flash (dự phòng tầng 3)

Tự động chuyển đổi mượt mà khi gặp lỗi 503 UNAVAILABLE, high demand, 429 RATE_LIMIT hoặc quá tải.
"""

import logging
from typing import Any, List, Optional
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service điều phối tập trung các mô hình Gemini với cơ chế Failover tự động."""

    def __init__(self):
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None and settings.GEMINI_API_KEY:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def get_model_pool(self, primary_model: Optional[str] = None) -> List[str]:
        """Trả về danh sách 4 model theo đúng thứ tự ưu tiên."""
        primary = primary_model or settings.LLM_MODEL_NAME
        pool = [primary]
        fallback_models = getattr(
            settings,
            "LLM_FALLBACK_MODELS",
            ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"],
        )
        for m in fallback_models:
            if m not in pool:
                pool.append(m)
        return pool

    @staticmethod
    def _is_recoverable_error(exc: Exception) -> bool:
        """Kiểm tra xem lỗi có phải do quá tải/tạm thời để tự động chuyển sang model khác."""
        err_str = str(exc).lower()
        return (
            "503" in err_str
            or "429" in err_str
            or "unavailable" in err_str
            or "resource_exhausted" in err_str
            or "high demand" in err_str
            or "overloaded" in err_str
            or "temporarily unavailable" in err_str
            or "quota" in err_str
            or "not found" in err_str
            or "404" in err_str
            or "timeout" in err_str
        )

    def generate_content(
        self,
        contents: Any,
        config: Optional[types.GenerateContentConfig] = None,
        primary_model: Optional[str] = None,
    ) -> Any:
        """
        Gọi generate_content với cơ chế tự động chuyển đổi qua lại giữa 4 model.
        """
        models = self.get_model_pool(primary_model)
        last_error = None

        for idx, model_name in enumerate(models):
            try:
                if idx > 0:
                    logger.warning(
                        "  [LLMService:Failover] Model trước quá tải. Tự động chuyển sang model dự phòng: [%s]",
                        model_name,
                    )

                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )

                if idx > 0:
                    logger.info("  [LLMService:Failover] Model dự phòng [%s] phản hồi THÀNH CÔNG!", model_name)

                return response

            except Exception as exc:
                last_error = exc
                if self._is_recoverable_error(exc) and idx < len(models) - 1:
                    logger.warning(
                        "  [LLMService:Failover] Model [%s] gặp sự cố (%s). Chuẩn bị thử model tiếp theo...",
                        model_name,
                        str(exc).split("\n")[0][:120],
                    )
                    continue
                raise exc

        if last_error:
            raise last_error

    def send_chat_message(
        self,
        prompt: str,
        tools: Optional[List[Any]] = None,
        temperature: float = 0.2,
        primary_model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Gửi tin nhắn chat kèm Agentic Tool Calling (AFC) có tự động chuyển đổi giữa 4 model.
        """
        models = self.get_model_pool(primary_model)
        last_error = None

        for idx, model_name in enumerate(models):
            try:
                if idx > 0:
                    logger.warning(
                        "  [LLMService:ChatFailover] Model trước quá tải. Tự động chuyển sang model: [%s] (tools=%s)",
                        model_name,
                        bool(tools),
                    )

                chat_config = (
                    types.GenerateContentConfig(tools=tools, temperature=temperature)
                    if tools
                    else types.GenerateContentConfig(temperature=temperature)
                )

                chat = self.client.chats.create(
                    model=model_name,
                    config=chat_config,
                )
                res = chat.send_message(prompt)
                if res and res.text:
                    if idx > 0:
                        logger.info("  [LLMService:ChatFailover] Model [%s] phản hồi THÀNH CÔNG!", model_name)
                    return res.text.strip()

            except Exception as exc:
                last_error = exc
                if self._is_recoverable_error(exc) and idx < len(models) - 1:
                    logger.warning(
                        "  [LLMService:ChatFailover] Model [%s] gặp sự cố (%s). Đang chuyển sang model tiếp theo...",
                        model_name,
                        str(exc).split("\n")[0][:120],
                    )
                    continue

                # Nếu là model cuối cùng hoặc lỗi khác, thử cứu vãn bằng generate_content thuần
                logger.warning("  [LLMService:ChatFailover] Chat thất bại với [%s], fallback sang generate_content...", model_name)
                try:
                    res = self.generate_content(contents=prompt, primary_model=model_name)
                    if res and res.text:
                        return res.text.strip()
                except Exception:
                    pass
                raise exc

        if last_error:
            raise last_error
        return None


llm_service = LLMService()
