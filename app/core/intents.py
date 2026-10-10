from enum import Enum
from typing import Dict, List, Any

from enum import Enum
from typing import Dict, List, Any

class IntentEnum(str, Enum):
    RENTZY_OVERVIEW = "rentzy_overview"
    RENT_OR_LIQUIDATION = "rent_or_liquidation"
    DEPOSIT_POLICY = "deposit_policy"
    RENTAL_PRICING = "rental_pricing"
    PRODUCT_PRICE = "product_price"
    PRODUCT_SEARCH = "product_search"
    RECEIVE_RETURN = "receive_return"
    DEPOSIT_REFUND = "deposit_refund"
    SHOWROOM_FITTING = "showroom_fitting"
    MEMBERSHIP = "membership"
    LIQUIDATION = "liquidation"
    CONTACT_SUPPORT = "contact_support"
    ORDER_SUPPORT = "order_support"
    FALLBACK = "fallback"

INTENT_CATALOG: Dict[str, Dict[str, Any]] = {
    IntentEnum.RENTZY_OVERVIEW.value: {
        "title": "Giới thiệu Rentzy & Dịch vụ",
        "description": "Các thông tin tổng quan, mô hình tủ đồ thời trang cho thuê, dịch vụ, địa chỉ showroom, hotline của Rentzy.",
        "keywords": ["rentzy", "giới thiệu", "thương hiệu", "dịch vụ", "mô hình", "tủ đồ thời trang", "showroom", "địa chỉ"],
        "examples": [
            "Rentzy là gì?",
            "Rentzy là dịch vụ gì vậy?",
            "Giới thiệu cho mình về Rentzy",
            "Mô hình cho thuê đồ hoạt động thế nào?",
            "Showroom của Rentzy ở đâu?"
        ]
    },
    IntentEnum.RENT_OR_LIQUIDATION.value: {
        "title": "Phân biệt Thuê hay Mua thanh lý",
        "description": "Tư vấn nhu cầu nên thuê đồ hay mua đồ thanh lý dựa trên số lần mặc và ngân sách.",
        "keywords": ["nên thuê hay mua", "thuê hay thanh lý", "tư vấn thuê hay mua", "tùy chọn thuê"],
        "examples": [
            "Tôi nên thuê hay mua thanh lý?",
            "Dùng 1 lần thì nên thuê hay mua?"
        ]
    },
    IntentEnum.DEPOSIT_POLICY.value: {
        "title": "Quy định & Hình thức đặt cọc",
        "description": "Các quy định về tiền cọc, cọc bằng CCCD hoặc tiền mặt, chính sách cọc giữ đồ.",
        "keywords": ["đặt cọc", "cọc", "phí cọc", "cọc cccd", "tiền cọc", "hinh_thuc_coc", "huy_coc_doi_mau"],
        "examples": [
            "Tôi có cần đặt cọc khi thuê không?",
            "Cọc bao nhiêu tiền?",
            "Có thể cọc bằng CCCD được không?",
            "Chính sách hủy cọc đổi mẫu"
        ]
    },
    IntentEnum.RENTAL_PRICING.value: {
        "title": "Bảng giá thuê & Thời gian thuê",
        "description": "Bảng giá thuê đồ theo ngày, thời gian tính gói thuê và chi phí phát sinh khi trễ hạn.",
        "keywords": ["bảng giá", "giá thuê", "thời gian thuê", "tính giá", "phát sinh", "trễ hạn"],
        "examples": [
            "Tính giá thuê đồ theo ngày như thế nào?",
            "Gói thuê bao gồm mấy ngày?",
            "Trả trễ hạn phạt bao nhiêu tiền?"
        ]
    },
    IntentEnum.PRODUCT_PRICE.value: {
        "title": "Tra cứu giá sản phẩm cụ thể",
        "description": "Hỏi giá thuê hoặc mua cụ thể cho từng loại trang phục (váy tiệc, đầm dạ hội, áo dài...).",
        "keywords": ["giá bao nhiêu", "hỏi giá", "hoi_gia", "nhiêu tiền", "bao tiền một bộ"],
        "examples": [
            "Đầm dạ hội này giá thuê bao nhiêu?",
            "Thuê áo dài cưới bao nhiêu tiền?"
        ]
    },
    IntentEnum.PRODUCT_SEARCH.value: {
        "title": "Tìm kiếm sản phẩm theo nhu cầu",
        "description": "Tìm kiếm mẫu trang phục theo chủ đề sự kiện, màu sắc, kích thước (size S, M, L).",
        "keywords": ["tìm mẫu", "tìm sản phẩm", "đầm đỏ", "váy trắng", "size s", "size m", "áo dài cưới"],
        "examples": [
            "Tìm giúp tôi đầm dự tiệc màu đỏ size M",
            "Có mẫu áo dài trắng nào không?",
            "Tìm váy dạ hội đen"
        ]
    },
    IntentEnum.RECEIVE_RETURN.value: {
        "title": "Giao nhận & Đổi trả trang phục",
        "description": "Quy trình shipper giao đồ, kiểm tra thử đồ khi nhận và quy trình hoàn trả trang phục.",
        "keywords": ["giao hàng", "nhận đồ", "trả đồ", "shipper", "thử khi nhận", "nhan_va_tra", "kiem_tra_khi_nhan"],
        "examples": [
            "Tôi có được thử đồ khi shipper giao đến không?",
            "Quy trình trả đồ sau khi dùng xong thế nào?"
        ]
    },
    IntentEnum.DEPOSIT_REFUND.value: {
        "title": "Thời gian & Chính sách hoàn cọc",
        "description": "Thời gian nhận lại tiền đặt cọc và điều kiện hoàn cọc sau khi Rentzy nhận lại đồ.",
        "keywords": ["hoàn cọc", "nhận lại cọc", "thoi_gian_hoan_coc", "hoàn tiền cọc", "trả lại cọc"],
        "examples": [
            "Bao lâu thì tôi nhận lại tiền đặt cọc?",
            "Sau khi trả đồ làm sao để nhận lại cọc?"
        ]
    },
    IntentEnum.SHOWROOM_FITTING.value: {
        "title": "Thử đồ trực tiếp tại Showroom",
        "description": "Hướng dẫn địa chỉ, thời gian mở cửa và đăng ký thử đồ trực tiếp tại Showroom Rentzy.",
        "keywords": ["thử đồ", "thu_do", "showroom", "đến cửa hàng", "thử trực tiếp", "địa chỉ tiệm"],
        "examples": [
            "Tôi có thể đến thử đồ trực tiếp tại showroom không?",
            "Showroom Rentzy mở cửa mấy giờ?"
        ]
    },
    IntentEnum.MEMBERSHIP.value: {
        "title": "Gói thành viên & Quyền lợi Membership",
        "description": "Thông tin các gói hội viên (Silver, Gold, VIP), mức phí đăng ký và quyền lợi ưu đãi.",
        "keywords": ["gói thành viên", "membership", "hội viên", "rentzy pass", "xem_goi", "chinh_sach"],
        "examples": [
            "Rentzy có các gói thành viên ưu đãi nào?",
            "Quyền lợi của gói hội viên VIP là gì?",
            "Các gói membership"
        ]
    },
    IntentEnum.LIQUIDATION.value: {
        "title": "Sản phẩm & Mua bán thanh lý",
        "description": "Danh mục sản phẩm thanh lý, mua lại trang phục cũ còn tốt từ Rentzy.",
        "keywords": ["thanh lý", "tly", "thanh ly", "mua đồ cũ", "pass đồ", "mua thanh lý"],
        "examples": [
            "Rentzy có bán thanh lý đồ cũ không?",
            "Xem đầm thanh lý ở đâu?",
            "Cho xin giá tly váy"
        ]
    },
    IntentEnum.CONTACT_SUPPORT.value: {
        "title": "Liên hệ hỗ trợ CSKH & Sales",
        "description": "Yêu cầu gặp trực tiếp chuyên viên tư vấn Sales, tổng đài hotline hoặc kênh CSKH.",
        "keywords": ["gặp tư vấn", "gặp nhân viên", "hotline", "cskh", "gặp người thật", "liên hệ sales", "tổng đài"],
        "examples": [
            "Tôi muốn gặp nhân viên tư vấn",
            "Cho tôi xin số hotline CSKH",
            "Nối máy cho người thật hỗ trợ"
        ]
    },
    IntentEnum.ORDER_SUPPORT.value: {
        "title": "Theo dõi & Hỗ trợ đơn hàng",
        "description": "Tra cứu mã đơn hàng, kiểm tra tiến độ giao hàng và điều chỉnh đơn đặt.",
        "keywords": ["theo dõi đơn", "mã đơn hàng", "đơn hàng của tôi", "kiểm tra đơn", "trạng thái đơn"],
        "examples": [
            "Tôi muốn kiểm tra trạng thái đơn hàng",
            "Đơn hàng của tôi đang ở đâu?"
        ]
    },
    IntentEnum.FALLBACK.value: {
        "title": "Ngoài phạm vi tri thức Rentzy",
        "description": "Các câu hỏi không liên quan đến dịch vụ thời trang và cho thuê của Rentzy.",
        "keywords": ["thời tiết", "chứng khoán", "tin tức", "bóng đá", "dịch tiếng anh", "viết code"],
        "examples": [
            "Hôm nay thời tiết thế nào?",
            "Giá cổ phiếu hôm nay tăng hay giảm?",
            "Dịch bài báo này giúp tôi"
        ]
    }
}

# 1. Từ điển chuẩn hóa từ viết tắt và tiếng lóng thời trang
ABBREVIATION_MAP: Dict[str, str] = {
    "cọc": "đặt cọc",
    "tly": "thanh lý",
    "thanh ly": "thanh lý",
    "pass": "thanh lý",
    "sm": "showroom",
    "pky": "phụ kiện",
    "đt": "đổi trả",
    "sp": "sản phẩm",
    "kh": "khách hàng",
    "cskh": "chăm sóc khách hàng",
    "mem": "thành viên",
    "nv": "nhân viên"
}

# 2. Ánh xạ Intent sang Topic trong CSDL Story 1 (Map 1-1 với 14 Topic Excel)
INTENT_TO_TOPIC_MAP: Dict[str, str] = {
    IntentEnum.RENTZY_OVERVIEW.value: "rentzy_overview",
    IntentEnum.RENT_OR_LIQUIDATION.value: "rent_or_liquidation",
    IntentEnum.DEPOSIT_POLICY.value: "deposit_policy",
    IntentEnum.RENTAL_PRICING.value: "rental_pricing",
    IntentEnum.PRODUCT_PRICE.value: "product_price",
    IntentEnum.PRODUCT_SEARCH.value: "product_search",
    IntentEnum.RECEIVE_RETURN.value: "receive_return",
    IntentEnum.DEPOSIT_REFUND.value: "deposit_refund",
    IntentEnum.SHOWROOM_FITTING.value: "showroom_fitting",
    IntentEnum.MEMBERSHIP.value: "membership",
    IntentEnum.LIQUIDATION.value: "liquidation",
    IntentEnum.CONTACT_SUPPORT.value: "contact_support",
    IntentEnum.ORDER_SUPPORT.value: "order_support",
    IntentEnum.FALLBACK.value: "fallback"
}


