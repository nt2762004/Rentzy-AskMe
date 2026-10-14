"""
Web Reader Service for fetching, parsing, and caching web page content.
Allows AI Agents to look up real-time web data and specific URLs.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

URL_REGEX = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)


class WebReaderService:
    """
    Dịch vụ tải và trích xuất nội dung văn bản từ URL web,
    hỗ trợ in-memory TTL caching để tối ưu tốc độ và tránh spam request.
    """

    def __init__(self, cache_ttl_seconds: int = 3600, timeout_seconds: float = 12.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self._cache: Dict[str, Tuple[float, str]] = {}

    def extract_urls(self, text: str) -> List[str]:
        """Trích xuất tất cả các đường link URL hợp lệ từ một đoạn văn bản."""
        if not text:
            return []
        matches = URL_REGEX.findall(text)
        # Loại bỏ dấu câu ở đuôi URL nếu có (như dấu chấm, phẩy, đóng ngoặc)
        cleaned_urls = []
        for url in matches:
            cleaned = url.rstrip(".,;!?)]}")
            if cleaned and cleaned not in cleaned_urls:
                cleaned_urls.append(cleaned)
        return cleaned_urls

    def fetch_url(self, url: str, max_chars: int = 3500) -> str:
        """
        Tải nội dung từ một URL, làm sạch mã HTML và trả về văn bản súc tích.
        Kết quả được lưu vào bộ nhớ đệm (cache) theo TTL.
        """
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return f"Đường dẫn không hợp lệ (URL phải bắt đầu bằng http:// hoặc https://): {url}"

        # 1. Kiểm tra cache
        now = time.time()
        if url in self._cache:
            timestamp, cached_content = self._cache[url]
            if now - timestamp < self.cache_ttl:
                logger.info("  └── [WebReader] Trả về nội dung từ Cache cho URL: %s", url)
                return cached_content

        # 2. Gửi request lấy HTML
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        logger.info("  └── [WebReader] Đang gửi HTTP GET tới: %s", url)
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                response = client.get(url)

            if response.status_code == 404:
                return f"Không tìm thấy trang web (Lỗi 404 - Not Found) tại đường link: {url}"
            elif response.status_code == 403:
                return f"Không có quyền truy cập trang web (Lỗi 403 - Forbidden) tại đường link: {url}"
            elif response.status_code >= 400:
                return f"Lỗi HTTP {response.status_code} khi tải trang: {url}"

            html_content = response.text
        except httpx.TimeoutException:
            logger.warning("  └── [WebReader] Quá thời gian chờ (Timeout) khi tải URL: %s", url)
            return f"Quá thời gian chờ (Timeout) khi kết nối tới đường link: {url}"
        except httpx.RequestError as exc:
            logger.error("  └── [WebReader] Lỗi kết nối HTTP (%s) tới URL: %s", exc, url)
            return f"Không thể kết nối tới đường link {url} ({exc})"
        except Exception as exc:
            logger.error("  └── [WebReader] Lỗi ngoại lệ (%s) khi xử lý URL: %s", exc, url)
            return f"Lỗi khi đọc nội dung từ {url} ({exc})"

        # 3. Làm sạch HTML và trích xuất text có ý nghĩa
        text = self._clean_html(html_content, max_chars=max_chars)
        if not text:
            text = f"Đã kết nối thành công tới {url} nhưng trang web không có nội dung văn bản hiển thị."

        # 4. Lưu vào cache
        self._cache[url] = (now, text)
        return text

    def _clean_html(self, html: str, max_chars: int = 3500) -> str:
        """Loại bỏ script, style, nav, footer và chuẩn hoá khoảng trắng."""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Loại bỏ các tag không liên quan đến nội dung chính
            for tag in soup(["script", "style", "noscript", "iframe", "svg", "header", "footer", "nav"]):
                tag.decompose()

            # Lấy text
            raw_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            clean_text = "\n".join(lines)

            # Rút gọn nếu vượt quá giới hạn ký tự
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars] + "\n... (Nội dung trang web đã được rút gọn súc tích)"

            return clean_text
        except Exception as exc:
            logger.warning("  └── [WebReader] Lỗi parse HTML (%s), fallback sang text thô", exc)
            return html[:max_chars]

    def clear_cache(self):
        """Xoá toàn bộ bộ nhớ cache."""
        self._cache.clear()


web_reader_service = WebReaderService()
