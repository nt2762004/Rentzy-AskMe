"""
Utilities for fast greeting detection and response formatting.
"""

import re
from typing import List

GREETING_WORDS = {
    "hello", "hi", "hey", "alo", "alô", "chào", "xin chào", "xin chao", "chao",
    "hế nhô", "helo", "hellu", "hí", "hola"
}

PRONOUNS_OR_NAMES = {
    "bạn", "ban", "shop", "rentzy", "ad", "admin", "em", "nàng", "nang",
    "cô", "anh", "chị", "chi", "mình", "minh", "cả nhà", "ca nha", "nha", "all"
}

PARTICLES = {
    "ạ", "a", "nha", "nhé", "nhe", "nè", "ne", "ơi", "oi", "nhở", "đó", "do",
    "ha", "á", "à", "nghen", "hen"
}

GREETING_PREFIX_PATTERNS = [
    # Dạ [,] [Rentzy] [xin] chào Nàng/bạn/quý khách/chị/em [ơi] [,!.-:]
    r"^(?:dạ\s*[,!.\-]?\s*)?(?:rentzy\s+)?(?:xin\s+)?chào\s+(?:nàng|bạn|quý\s+khách|chị|em)(?:\s+ơi)?(?:\s*[,!.\-:]+\s*|\s+)",
    # Rentzy xin chào Nàng/bạn [ơi] [,!.-:]
    r"^rentzy\s+(?:xin\s+)?chào\s+(?:nàng|bạn)(?:\s+ơi)?(?:\s*[,!.\-:]+\s*|\s+)",
    # Dạ Nàng ơi / Dạ Nàng! / Dạ Nàng,
    r"^dạ\s+nàng(?:\s+ơi)?(?:\s*[,!.\-:]+\s*|\s+)",
    # Dạ, / Dạ! ở đầu câu
    r"^dạ\s*[,!]\s*",
]

FAST_REPLY_GREETING_MESSAGE = (
    "Dạ Rentzy xin chào Nàng! Rentzy có thể hỗ trợ Nàng tìm hiểu về dịch vụ cho thuê trang phục, "
    "các gói thành viên hay thông tin nào hôm nay ạ?"
)

FAST_REPLY_CONTINUATION_GREETING_MESSAGE = (
    "Dạ Rentzy đây ạ! Nàng đang cần mình hỗ trợ thông tin gì tiếp theo ạ?"
)

FAST_REPLY_SUGGESTED_OPTIONS: List[str] = [
    "Gói thành viên",
    "Bảng giá thuê",
    "Địa chỉ Showroom",
    "Gặp tư vấn viên",
]


def is_simple_greeting(text: str) -> bool:
    """
    Kiểm tra xem câu của người dùng có phải là lời chào hỏi đơn thuần
    (không kèm câu hỏi nghiệp vụ / tra cứu thông tin) hay không.
    Ví dụ: 'hello', 'xin chào shop', 'alo rentzy', 'shop ơi', 'chào bạn nha'.
    """
    if not text:
        return False
    raw = text.strip().lower()
    # Loại bỏ dấu câu
    clean = re.sub(r"[.,!?;:~\-_\^]+", " ", raw).strip()
    if not clean:
        return False

    tokens = clean.split()
    if len(tokens) > 6:
        # Câu chào đơn thuần thường không dài quá 6 từ
        return False

    clean_collapsed = " ".join(tokens)

    # 1. Các mẫu gọi tên đơn giản: 'shop ơi', 'rentzy ơi', 'ad ơi'
    if re.match(r"^(?:rentzy|shop|ad|admin)\s+(?:ơi|oi|ạ|a)(?:\s+(?:ạ|a|nha|nhé|nhe))?$", clean_collapsed):
        return True

    # 2. Bắt đầu bằng từ chào
    is_greeting_start = False
    idx = 0
    if clean_collapsed.startswith("xin chào") or clean_collapsed.startswith("xin chao"):
        is_greeting_start = True
        idx = 2
    elif clean_collapsed.startswith("hế nhô") or clean_collapsed.startswith("he nho"):
        is_greeting_start = True
        idx = 2
    else:
        first_token = tokens[0]
        if first_token in GREETING_WORDS or re.match(r"^(?:alo+|alô+|hi+|hey+|helo+|hellu+)$", first_token):
            is_greeting_start = True
            idx = 1

    if not is_greeting_start:
        return False

    # Các từ còn lại sau từ chào phải thuộc danh xưng hoặc thán từ/từ đệm
    remaining_tokens = tokens[idx:]
    i = 0
    while i < len(remaining_tokens):
        if i + 1 < len(remaining_tokens) and f"{remaining_tokens[i]} {remaining_tokens[i+1]}" in PRONOUNS_OR_NAMES:
            i += 2
            continue
        token = remaining_tokens[i]
        if token in PRONOUNS_OR_NAMES or token in PARTICLES:
            i += 1
            continue
        return False

    return True


def strip_opening_greeting(text: str) -> str:
    """
    Loại bỏ câu chào mở đầu lặp lại ở đầu phản hồi (ví dụ 'Chào Nàng,', 'Dạ chào Nàng!')
    trong các lượt trao đổi tiếp theo của phiên chat để tránh cảm giác máy móc lặp lại.
    """
    if not text:
        return text
    result = text.strip()
    for pattern in GREETING_PREFIX_PATTERNS:
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            result = result[match.end():].strip()
            # Kiểm tra xem có còn sót thêm cụm chào kép nữa không
            second_match = re.search(pattern, result, re.IGNORECASE)
            if second_match:
                result = result[second_match.end():].strip()
            break

    if result:
        # Viết hoa chữ cái đầu tiên của câu sau khi cắt bỏ lời chào
        result = result[0].upper() + result[1:]
    return result
