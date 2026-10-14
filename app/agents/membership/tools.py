"""
Tools for Membership Agent — Tra cứu thông tin trên web và link cụ thể.
"""

import logging
from app.services.web_reader import web_reader_service

logger = logging.getLogger(__name__)


def fetch_web_page(url: str) -> str:
    """Truy cập và đọc nội dung văn bản thực tế từ một trang web hoặc đường link URL cụ thể trên internet (ví dụ trang thông tin gói membership https://rentzy.vn/member-ship/ hoặc link bài viết, chương trình ưu đãi) để lấy dữ liệu mới nhất.

    Args:
        url: Đường link URL đầy đủ cần tra cứu (ví dụ: https://rentzy.vn/member-ship/).
    """
    logger.info("  └── [MembershipAgent:Tool] Kích hoạt tool fetch_web_page(url='%s')", url)
    return web_reader_service.fetch_url(url)
