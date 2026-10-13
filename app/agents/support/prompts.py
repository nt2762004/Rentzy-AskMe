"""
Prompts, constants, and templates for Support Agent.
"""

from typing import Dict

HOTLINE_NUMBER = "0798969040"
SHOWROOM_ADDRESS = "51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"
SUPPORT_HOURS = "09:00 - 21:00 (Tất cả các ngày trong tuần)"
ZALO_URL = "https://zalo.me/0798969040"
FANPAGE_URL = "https://facebook.com/rentzy.vn"

# Sub-intent descriptions
SUPPORT_SUB_INTENTS: Dict[str, str] = {
    "hotline_call":   "Khách xin số điện thoại Hotline CSKH để liên hệ trực tiếp",
    "human_agent":    "Khách muốn gặp trực tiếp nhân viên tư vấn / chat với người thật",
    "order_support":  "Khách cần tra cứu, hỗ trợ hoặc kiểm tra đơn hàng thuê",
    "complaint":      "Khách phản ánh sự cố đồ thuê, đổi đồ gấp hoặc khiếu nại dịch vụ",
    "general":        "Các yêu cầu hỗ trợ chung khác",
}

# Sub-intent guidance for LLM
SUPPORT_SUB_INTENT_FOCUS: Dict[str, str] = {
    "hotline_call": (
        f"Hãy cung cấp ngay Hotline hỗ trợ trực tiếp của Rentzy:\n"
        f"- Hotline: {HOTLINE_NUMBER}\n"
        f"- Địa chỉ Showroom: {SHOWROOM_ADDRESS}\n"
        "Hướng dẫn khách có thể gọi trực tiếp hoặc nhấn nút Chat Zalo bên dưới để được giải đáp tức thì."
    ),
    "human_agent": (
        f"Hãy thông báo sẵn sàng kết nối với chuyên viên tư vấn của Rentzy qua:\n"
        f"- Hotline: {HOTLINE_NUMBER}\n"
        f"- Địa chỉ Showroom: {SHOWROOM_ADDRESS}\n"
        "Nhắc khách có thể gọi Hotline hoặc nhấn nút Chat Zalo ngay bên dưới để gặp trực tiếp nhân viên tư vấn."
    ),
    "order_support": (
        f"Hãy hướng dẫn khách gửi Mã đơn hàng (hoặc Số điện thoại đặt hàng) "
        f"qua Hotline {HOTLINE_NUMBER} hoặc nút Chat Zalo bên dưới để nhân viên tra cứu nhanh trạng thái giao nhận và xử lý ngay cho Nàng."
    ),
    "complaint": (
        f"Hãy thể hiện sự đồng cảm, lịch sự và lắng nghe phản ánh của khách. "
        f"Cung cấp Hotline {HOTLINE_NUMBER} hoặc hướng dẫn khách nhấn nút Chat Zalo bên dưới để Rentzy ưu tiên xử lý đổi mẫu hoặc giải quyết khiếu nại ngay lập tức."
    ),
    "general": (
        f"Hãy hỗ trợ giải đáp thắc mắc và cung cấp thông tin liên hệ:\n"
        f"- Hotline: {HOTLINE_NUMBER}\n"
        f"- Địa chỉ Showroom: {SHOWROOM_ADDRESS}"
    ),
}

SUPPORT_FALLBACK_REPLY = (
    "Dạ Nàng! Để được hỗ trợ trực tiếp và nhanh nhất từ đội ngũ chăm sóc khách hàng Rentzy, Nàng có thể liên hệ qua:\n\n"
    f"- Hotline: {HOTLINE_NUMBER}\n"
    f"- Địa chỉ Showroom: {SHOWROOM_ADDRESS}\n\n"
    "Hoặc Nàng có thể nhấn nút Chat Zalo ngay bên dưới để gặp nhân viên hỗ trợ nhé!"
)


def build_support_prompt(context_str: str, message: str, sub_intent: str) -> str:
    """
    Tạo prompt chuẩn cho Support Agent.
    """
    focus = SUPPORT_SUB_INTENT_FOCUS.get(sub_intent, SUPPORT_SUB_INTENT_FOCUS["general"])

    return (
        "Bạn là Trợ lý AI AskMe của thương hiệu thời trang Rentzy — chuyên viên Hỗ trợ & Chăm sóc khách hàng (Support Agent).\n\n"
        f"[Nhiệm vụ chính]: {focus}\n\n"
        "[Yêu cầu phong cách & Trình bày]:\n"
        "- Xưng 'Rentzy' hoặc 'mình', gọi khách là 'Nàng'.\n"
        "- Trả lời NGẮN GỌN, TẬN TÂM, ĐI THẲNG VÀO GIẢI PHÁP — tối đa 3-4 câu hoặc 2-3 gạch đầu dòng (-) rõ ràng.\n"
        "- BẮT BUỘC chỉ liệt kê 2 kênh liên hệ trên từng dòng riêng:\n"
        f"  - Hotline: {HOTLINE_NUMBER}\n"
        f"  - Địa chỉ Showroom: {SHOWROOM_ADDRESS}\n"
        "- Tuyệt đối KHÔNG viết đường link hay dòng 'Zalo hỗ trợ' trong văn bản (vì giao diện đã có sẵn nút bấm Chat Zalo ngay bên dưới).\n"
        "- Tuyệt đối không dùng các icon lấp lánh rườm rà (✨, emoji trang trí không cần thiết).\n\n"
        f"[Thông tin chính thức Rentzy]:\n{context_str}\n\n"
        f"[Câu hỏi của khách hàng]: \"{message}\"\n"
    )
