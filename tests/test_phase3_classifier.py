import pytest
from app.services.classifier import intent_classifier
from app.core.intents import IntentEnum

def test_phase3_classification_all_14_intents():
    """Kiểm tra khả năng phân loại của Phase 3 cho các câu hỏi đại diện của 14 Intent."""
    test_cases = [
        ("Giới thiệu Rentzy đi bạn", IntentEnum.RENTZY_OVERVIEW.value),
        ("Tôi nên thuê hay mua đồ thanh lý?", IntentEnum.RENT_OR_LIQUIDATION.value),
        ("Cọc cccd như thế nào bạn?", IntentEnum.DEPOSIT_POLICY.value),
        ("Tính giá thuê đồ theo ngày như thế nào?", IntentEnum.RENTAL_PRICING.value),
        ("Đầm dạ hội này giá bao nhiêu?", IntentEnum.PRODUCT_PRICE.value),
        ("Tìm cho mình mẫu váy màu đỏ size M", IntentEnum.PRODUCT_SEARCH.value),
        ("Quy trình nhận đồ và trả đồ như nào?", IntentEnum.RECEIVE_RETURN.value),
        ("Bao lâu thì hoàn tiền cọc cho mình?", IntentEnum.DEPOSIT_REFUND.value),
        ("Thử đồ tại showroom quận 4", IntentEnum.SHOWROOM_FITTING.value),
        ("Quyền lợi gói thành viên VIP là gì?", IntentEnum.MEMBERSHIP.value),
        ("Rentzy có thanh lý đồ cũ giá rẻ không?", IntentEnum.LIQUIDATION.value),
        ("Cho mình xin số hotline cskh gặp người thật", IntentEnum.CONTACT_SUPPORT.value),
        ("Tôi muốn kiểm tra trạng thái đơn hàng", IntentEnum.ORDER_SUPPORT.value),
        ("Dịch bài báo tiếng Anh này giúp tôi", IntentEnum.FALLBACK.value),
    ]

    for question, expected_intent in test_cases:
        res = intent_classifier.classify(question)
        assert res.intent == expected_intent, f"Câu hỏi '{question}' kỳ vọng {expected_intent} nhưng nhận được {res.intent}"
        assert res.confidence > 0.60

def test_phase3_abbreviation_handling():
    """Kiểm tra xử lý các từ viết tắt phổ biến trong thời trang Việt Nam."""
    res_coc = intent_classifier.classify("Cọc như nào bạn")
    assert res_coc.intent in [IntentEnum.DEPOSIT_POLICY.value, IntentEnum.DEPOSIT_REFUND.value]

    res_tly = intent_classifier.classify("Cho xin giá tly váy pass")
    assert res_tly.intent == IntentEnum.LIQUIDATION.value

def test_phase3_ambiguous_and_multi_intent():
    """Kiểm tra xử lý câu hỏi mơ hồ hoặc chứa nhiều ý định."""
    res = intent_classifier.classify("Tôi muốn xem")
    assert res.need_clarification is True or res.confidence < 0.90
