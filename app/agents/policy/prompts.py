"""
Prompts, constants, and templates for Policy Agent.
"""

from typing import Dict

HOTLINE_NUMBER = "0798969040"
SHOWROOM_ADDRESS = "51 đường số 41, phường Khánh Hội, TP. Hồ Chí Minh"

# Key policy highlights
DEPOSIT_RULES_SUMMARY = (
    "- Hình thức cọc: Có thể cọc bằng tiền mặt hoặc giữ Căn cước công dân (CCCD) bản gốc.\n"
    "- Số tiền cọc: Tùy theo giá trị của trang phục (thông thường từ 500k - 2 triệu đồng/bộ).\n"
    "- Đổi mẫu/Hủy cọc: Hỗ trợ đổi mẫu trước ngày lấy đồ ít nhất 24h - 48h."
)

DEPOSIT_REFUND_SUMMARY = (
    "- Thời gian hoàn cọc: Trong vòng 24h kể từ khi Rentzy nhận lại đồ và kiểm tra hoàn tất.\n"
    "- Hình thức hoàn: Chuyển khoản trực tiếp vào tài khoản ngân hàng của Nàng."
)

RECEIVE_RETURN_SUMMARY = (
    "- Giao nhận: Nhận trực tiếp tại showroom hoặc giao qua các đơn vị vận chuyển (Ahamove/Grab).\n"
    "- Giặt ủi: Nàng KHÔNG CẦN giặt ủi trước khi trả; Rentzy sẽ giặt hấp và chăm sóc trang phục chuyên nghiệp.\n"
    "- Kiểm tra đồ: Vui lòng kiểm tra kỹ tình trạng váy khi nhận và báo ngay cho Rentzy nếu có lỗi."
)

RENTAL_PRICING_SUMMARY = (
    "- Thời gian thuê tiêu chuẩn: Gói 3 ngày 2 đêm (nhận đồ hôm trước, mặc hôm sự kiện, trả đồ hôm sau).\n"
    "- Trễ hạn: Nếu trả trễ so với hạn đã đăng ký, phụ phí sẽ tính theo ngày phát sinh theo bảng giá."
)

POLICY_SUB_INTENTS: Dict[str, str] = {
    "deposit_rules":      "Quy định đặt cọc, cọc CCCD hoặc tiền mặt, hủy cọc đổi mẫu",
    "deposit_refund":     "Thời gian và chính sách hoàn trả tiền cọc sau khi trả đồ",
    "rental_pricing":     "Bảng giá thuê đồ, thời gian thuê tiêu chuẩn và phí trễ hạn",
    "receive_and_return": "Quy trình giao nhận đồ, kiểm tra đồ và trả đồ không cần giặt",
    "general":            "Quy định và chính sách thuê đồ Rentzy chung",
}

POLICY_SUB_INTENT_FOCUS: Dict[str, str] = {
    "deposit_rules": (
        f"Hãy giải thích rõ ràng chính sách đặt cọc của Rentzy:\n{DEPOSIT_RULES_SUMMARY}\n"
        "Nhấn mạnh khách có thể linh hoạt chọn cọc tiền hoặc CCCD bản gốc."
    ),
    "deposit_refund": (
        f"Hãy giải thích rõ ràng chính sách hoàn cọc:\n{DEPOSIT_REFUND_SUMMARY}\n"
        "Đảm bảo khách yên tâm tiền cọc sẽ được chuyển khoản nhanh chóng sau khi kiểm tra đồ."
    ),
    "rental_pricing": (
        f"Hãy giải thích thời gian và bảng giá thuê:\n{RENTAL_PRICING_SUMMARY}\n"
        "Nhắc khách thuê theo gói 3 ngày 2 đêm để thoải mái chuẩn bị dự tiệc."
    ),
    "receive_and_return": (
        f"Hãy giải thích quy trình nhận và trả đồ:\n{RECEIVE_RETURN_SUMMARY}\n"
        "Đặc biệt nhấn mạnh Nàng KHÔNG CẦN GIẶT ỦI trước khi trả đồ."
    ),
    "general": (
        "Hãy giải đáp thắc mắc về chính sách thuê trang phục của Rentzy một cách ngắn gọn, rõ ràng và minh bạch."
    ),
}

POLICY_FALLBACK_REPLY = (
    "Dạ Rentzy hỗ trợ đặt cọc linh hoạt bằng tiền mặt hoặc CCCD bản gốc. "
    "Sau khi trả đồ, tiền cọc sẽ được hoàn lại trong vòng 24h qua chuyển khoản. "
    f"Nàng có thể liên hệ Hotline {HOTLINE_NUMBER} để được tư vấn chi tiết hơn nhé!"
)


def build_policy_prompt(context_str: str, message: str, sub_intent: str) -> str:
    """
    Tạo prompt chuẩn cho Policy Agent.
    """
    focus = POLICY_SUB_INTENT_FOCUS.get(sub_intent, POLICY_SUB_INTENT_FOCUS["general"])

    return (
        "Bạn là Trợ lý AI AskMe của thương hiệu thời trang Rentzy — chuyên gia tư vấn Chính sách & Quy định thuê (Policy Agent).\n\n"
        f"[Nhiệm vụ chính]: {focus}\n\n"
        "[Yêu cầu phong cách & Trình bày]:\n"
        "- Xưng 'Rentzy' hoặc 'mình', gọi khách là 'Nàng'.\n"
        "- Trả lời NGẮN GỌN, TRỰC TIẾP, MINH BẠCH — tối đa 3-4 câu hoặc 2-3 gạch đầu dòng (-) súc tích nhất.\n"
        "- Khi liệt kê các ý/quy định, BẮT BUỘC dùng gạch đầu dòng (-) ở đầu mỗi dòng.\n"
        "- Nhấn mạnh các điểm tiện lợi cho khách (ví dụ: cọc CCCD không cần tiền mặt, không cần giặt ủi khi trả).\n"
        "- Tuyệt đối không dùng emoji rườm rà (✨, hoa lá).\n\n"
        f"[Thông tin chính thức Rentzy]:\n{context_str}\n\n"
        f"[Câu hỏi của khách hàng]: \"{message}\"\n"
    )
