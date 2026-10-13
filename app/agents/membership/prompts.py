"""
Prompts, constants, and templates for Membership Agent.
"""

from typing import Dict

MEMBERSHIP_REGISTER_URL = "https://rentzy.vn/member-ship/"

# Sub-intent descriptions
MEMBERSHIP_SUB_INTENTS: Dict[str, str] = {
    "overview":  "Hỏi tổng quan về các gói thành viên, có những gói gì",
    "pricing":   "Hỏi giá phí đăng ký từng gói (Silver, Gold, VIP)",
    "benefits":  "Hỏi quyền lợi / ưu đãi cụ thể của gói",
    "register":  "Muốn đăng ký / tham gia gói thành viên",
    "compare":   "So sánh các gói với nhau",
    "renew":     "Hỏi về gia hạn hoặc nâng cấp gói",
}

# Sub-intent task focus guidance for LLM
SUB_INTENT_FOCUS: Dict[str, str] = {
    "overview": "Hãy giới thiệu tổng quan các gói thành viên hiện có của Rentzy (tên gói, điểm nổi bật).",
    "pricing":  "Hãy trả lời RÕ RÀNG về mức phí / giá của từng gói thành viên.",
    "benefits": "Hãy liệt kê chi tiết quyền lợi và ưu đãi mà thành viên nhận được.",
    "register": "Hãy hướng dẫn ngắn gọn cách đăng ký gói thành viên và đính kèm link đăng ký.",
    "compare":  "Hãy so sánh ngắn gọn sự khác biệt giữa các gói (Silver, Gold, VIP) theo dạng gạch đầu dòng.",
    "renew":    "Hãy trả lời về cách gia hạn hoặc nâng cấp gói thành viên.",
}

MEMBERSHIP_FALLBACK_REPLY = (
    "Dạ Rentzy có các gói thành viên Silver, Gold và VIP với nhiều ưu đãi thuê trang phục hấp dẫn ạ. "
    "Nàng có thể xem chi tiết và đăng ký tại link bên dưới nhé!"
)


def build_membership_prompt(context_str: str, message: str, sub_intent: str) -> str:
    """
    Tạo prompt chuẩn chỉnh cho Gemini xử lý riêng biệt intent Membership.
    """
    focus = SUB_INTENT_FOCUS.get(sub_intent, SUB_INTENT_FOCUS["overview"])

    return (
        "Bạn là Trợ lý AI AskMe của thương hiệu thời trang Rentzy — chuyên gia về Gói thành viên (Membership).\n\n"
        f"[Nhiệm vụ chính]: {focus}\n\n"
        "[Yêu cầu phong cách & Trình bày]:\n"
        "- Xưng 'Rentzy' hoặc 'mình', gọi khách là 'Nàng'.\n"
        "- Trả lời NGẮN GỌN, TRỰC TIẾP — tối đa 4-5 gạch đầu dòng hoặc 3-4 câu súc tích.\n"
        "- Dùng dấu gạch đầu dòng (-) khi liệt kê gói, quyền lợi, mức phí.\n"
        "- Cuối câu trả lời BẮT BUỘC thêm dòng sau (nguyên văn):\n"
        f"  {MEMBERSHIP_REGISTER_URL}\n"
        "- Tuyệt đối không dùng icon trang trí không cần thiết.\n\n"
        f"[Thông tin chính thức Rentzy về Membership]:\n{context_str}\n\n"
        f"[Câu hỏi của khách hàng]: \"{message}\"\n"
    )
