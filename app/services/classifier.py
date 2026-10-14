import json
import logging
import warnings
warnings.filterwarnings("ignore")

from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.intents import INTENT_CATALOG, IntentEnum

logger = logging.getLogger(__name__)

class IntentClassificationResult(BaseModel):
    intent: str = Field(..., description="Mã Intent chuẩn (1 trong 12 mã trong INTENT_CATALOG)")
    confidence: float = Field(..., description="Độ tin cậy từ 0.00 đến 1.00")
    need_clarification: bool = Field(default=False, description="True nếu câu hỏi quá mơ hồ hoặc chứa nhiều ý định")
    suggested_options: Optional[List[str]] = Field(default=None, description="Danh sách các lựa chọn làm rõ")
    reasoning: Optional[str] = Field(default=None, description="Giải thích lý do nhận diện")

class IntentClassifierService:
    def __init__(self):
        self._client: Optional[genai.Client] = None
        if settings.GEMINI_API_KEY:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def classify(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> IntentClassificationResult:
        """
        Phân loại câu hỏi của người dùng vào 1 trong 12 Intent bằng Google Gemini Flash Lite.
        Hỗ trợ nhận diện từ viết tắt, lỗi chính tả, mơ hồ và multi-intent.
        """
        # 1. Rule-based heuristic check trước cho câu từ ngắn/rõ ràng
        normalized_msg = message.strip().lower()
        
        # Check liên hệ Sales trực tiếp
        if any(kw in normalized_msg for kw in ["gặp nhân viên", "nói chuyện người thật", "gặp tư vấn", "gọi hotline", "cho xin số cskh", "nhân viên tư vấn", "tư vấn viên", "chuyên viên tư vấn"]):
            return IntentClassificationResult(
                intent=IntentEnum.CONTACT_SUPPORT.value,
                confidence=0.98,
                reasoning="Rule-based keyword match for Contact Support"
            )

        # Check gói thành viên / membership
        if any(kw in normalized_msg for kw in ["gói thành viên", "membership", "member-ship", "hội viên", "rentzy.vn/member-ship", "gói silver", "gói gold", "gói vip"]):
            return IntentClassificationResult(
                intent=IntentEnum.MEMBERSHIP.value,
                confidence=0.98,
                reasoning="Rule-based keyword match for Membership"
            )

        # 2. Tạo prompt hệ thống với danh mục 14 Intent
        intent_descriptions = "\n".join([
            f"- `{code}` ({info['title']}): {info['description']} (Từ khóa tiêu biểu: {', '.join(info['keywords'][:5])})"
            for code, info in INTENT_CATALOG.items()
        ])

        system_instruction = f"""Bạn là Bộ phân loại Ý định (Intent Classifier Engine) cho Chatbot của thương hiệu thời trang Rentzy.
Nhiệm vụ của bạn là phân tích câu hỏi tự nhiên của khách hàng (có thể chứa từ viết tắt như 'cọc', 'tly', 'sm', 'pky', lỗi chính tả) và xếp vào đúng 1 trong 14 Intent sau:

{intent_descriptions}

Quy tắc phân loại:
1. Nếu câu hỏi có từ viết tắt (VD: 'cọc' = đặt cọc, 'tly' = thanh lý, 'sm' = showroom, 'pky' = phụ kiện), bạn phải hiểu đúng ngữ nghĩa thời trang.
2. Nếu câu hỏi quá ngắn, mơ hồ hoặc có thể thuộc nhiều hơn 1 Intent (Multi-intent), đặt `need_clarification` = true và gợi ý `suggested_options`.
3. Tính toán `confidence` từ 0.00 đến 1.00. Nếu không liên quan đến Rentzy hoặc thời trang (VD: thời tiết, toán học), xếp vào `fallback` với confidence = 1.00.

BẮT BUỘC TRẢ VỀ DẠNG JSON SCHEMA CHÍNH XÁC:
{{
  "intent": "mã_intent_1_trong_14",
  "confidence": 0.95,
  "need_clarification": false,
  "suggested_options": ["Gợi ý 1", "Gợi ý 2"],
  "reasoning": "Lý do phân loại"
}}
"""

        prompt = f"Câu hỏi của khách hàng: \"{message}\""
        if chat_history and len(chat_history) > 0:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in chat_history[-3:]])
            prompt = f"Ngữ cảnh hội thoại gần đây:\n{history_str}\n\n{prompt}"

        try:
            response = self._client.models.generate_content(
                model=settings.LLM_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            result_dict = json.loads(response.text)
            intent_code = result_dict.get("intent", IntentEnum.FALLBACK.value)
            if intent_code not in INTENT_CATALOG:
                intent_code = IntentEnum.FALLBACK.value


            return IntentClassificationResult(
                intent=intent_code,
                confidence=float(result_dict.get("confidence", 0.85)),
                need_clarification=bool(result_dict.get("need_clarification", False)),
                suggested_options=result_dict.get("suggested_options"),
                reasoning=result_dict.get("reasoning")
            )

        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini Intent Classifier ({e}). Fallback về Heuristic matching!")
            # Fallback heuristic: chọn intent có từ khóa khớp đặc thù nhất (tổng độ dài match cao nhất)
            best_intent = None
            best_score = 0
            for code, info in INTENT_CATALOG.items():
                matched_kws = [kw for kw in info.get("keywords", []) if kw in normalized_msg]
                if matched_kws:
                    score = sum(len(kw) for kw in matched_kws)
                    if score > best_score:
                        best_score = score
                        best_intent = code

            if best_intent:
                return IntentClassificationResult(
                    intent=best_intent,
                    confidence=0.75,
                    reasoning="Fallback keyword match"
                )

            return IntentClassificationResult(
                intent=IntentEnum.FALLBACK.value,
                confidence=0.50,
                reasoning="Fallback default out of scope"
            )

intent_classifier = IntentClassifierService()
