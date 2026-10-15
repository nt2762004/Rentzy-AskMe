"""
Unified LLM Service with automatic failover to backup models.
Tự động chuyển sang model dự phòng (gemini-flash-lite-latest, gemini-3.5-flash-lite) khi model chính (Gemini 3.1 Flash Lite) bị quá tải (503 UNAVAILABLE / 429 RATE_LIMIT).
"""

import logging
from typing import Any, List, Optional
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service tập trung gọi Gemini LLM với cơ chế Failover đa tầng."""

    def __init__(self):
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None and settings.GEMINI_API_KEY:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def generate_content(
        self,
        contents: Any,
        config: Optional[types.GenerateContentConfig] = None,
        primary_model: Optional[str] = None,
    ) -> Any:
        """
        Gọi mô hình Gemini tạo nội dung / phân loại ý định / gọi công cụ (AFC).
        Nếu model chính (gemini-3.1-flash-lite) bị quá tải (503, 429, high demand),
        sẽ tự động bắt lỗi và thử lần lượt các model dự phòng.
        """
        primary = primary_model or settings.LLM_MODEL_NAME
        candidates: List[str] = [primary]
        for m in settings.LLM_FALLBACK_MODELS:
            if m not in candidates:
                candidates.append(m)

        last_error = None
        for idx, model_name in enumerate(candidates):
            try:
                if idx > 0:
                    logger.warning(
                        "  [LLMService:Failover] Model chính quá tải hoặc lỗi. Đang chuyển sang model dự phòng: [%s]",
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
                err_str = str(exc)
                # Kiểm tra các lỗi quá tải hoặc mạng có thể phục hồi bằng model khác
                is_recoverable = (
                    "503" in err_str
                    or "429" in err_str
                    or "UNAVAILABLE" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "high demand" in err_str.lower()
                    or "overloaded" in err_str.lower()
                    or "temporarily unavailable" in err_str.lower()
                    or "not found" in err_str.lower()
                    or "404" in err_str
                )

                if is_recoverable and idx < len(candidates) - 1:
                    logger.warning(
                        "  [LLMService:Error] Model [%s] gặp lỗi (%s). Chuẩn bị thử model tiếp theo...",
                        model_name,
                        err_str.split("\n")[0][:100],
                    )
                    continue
                else:
                    raise exc

        if last_error:
            raise last_error


llm_service = LLMService()
