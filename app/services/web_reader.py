"""
Web Reader Service for fetching, parsing, and caching web page content.
Allows AI Agents to look up real-time web data and specific URLs.
Caches fetched content directly in Redis with automatic TTL and in-memory fallback.
"""

import re
import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
from redis import Redis

from app.core.config import settings

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
    lưu trữ bộ nhớ đệm (cache) trực tiếp trên Redis với TTL tự động,
    đồng thời hỗ trợ fallback sang bộ nhớ RAM (In-Memory) nếu Redis gián đoạn.
    """

    def __init__(self, cache_ttl_seconds: int = 3600, timeout_seconds: float = 12.0):
        self.cache_ttl = cache_ttl_seconds
        self.timeout = timeout_seconds
        self._memory_cache: Dict[str, Tuple[float, str]] = {}
        self._redis_client: Optional[Redis] = None
        self._init_redis()

    def _init_redis(self):
        """Khởi tạo kết nối tới Redis cache theo cấu hình hệ thống."""
        try:
            if settings.REDIS_HOST:
                client = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD or None,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_timeout=5,
                )
            elif settings.REDIS_URL:
                client = Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=5)
            else:
                client = Redis(host="localhost", port=6379, db=0, decode_responses=True, socket_timeout=2)
            client.ping()
            self._redis_client = client
            logger.info("  └── [WebReader:Redis] Kết nối Redis Web Cache thành công!")
        except Exception as exc:
            logger.warning("  └── [WebReader:Redis] Không thể kết nối Redis (%s). Fallback sang In-Memory Cache!", exc)
            self._redis_client = None

    def _get_redis_key(self, url: str) -> str:
        """Tạo khóa Redis chuẩn hóa theo namespace cho từng URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return f"rentzy:web_cache:{url_hash}"

    def _get_cached(self, url: str) -> Optional[str]:
        """Lấy nội dung cache từ Redis hoặc In-Memory."""
        # 1. Đọc từ Redis
        if self._redis_client:
            try:
                cached = self._redis_client.get(self._get_redis_key(url))
                if cached:
                    logger.info("  └── [WebReader:Redis] Cache HIT (Redis) cho URL: %s", url)
                    return cached
            except Exception as exc:
                logger.warning("  └── [WebReader:Redis] Lỗi khi đọc Redis cache (%s), thử In-Memory", exc)

        # 2. Fallback sang In-Memory nếu Redis không khả dụng
        now = time.time()
        if url in self._memory_cache:
            ts, val = self._memory_cache[url]
            if now - ts < self.cache_ttl:
                logger.info("  └── [WebReader:Cache] Cache HIT (In-Memory) cho URL: %s", url)
                return val
        return None

    def _set_cached(self, url: str, content: str):
        """Lưu nội dung vào Redis với thời hạn TTL tự động hết hạn."""
        # 1. Lưu vào Redis
        if self._redis_client:
            try:
                self._redis_client.set(self._get_redis_key(url), content, ex=self.cache_ttl)
                logger.info("  └── [WebReader:Redis] Đã lưu cache vào Redis (TTL=%ds) cho URL: %s", self.cache_ttl, url)
                return
            except Exception as exc:
                logger.warning("  └── [WebReader:Redis] Lỗi khi ghi Redis cache (%s), fallback In-Memory", exc)

        # 2. Fallback sang In-Memory
        self._memory_cache[url] = (time.time(), content)

    def extract_urls(self, text: str) -> List[str]:
        """Trích xuất tất cả các đường link URL hợp lệ từ một đoạn văn bản."""
        if not text:
            return []
        matches = URL_REGEX.findall(text)
        cleaned_urls = []
        for url in matches:
            cleaned = url.rstrip(".,;!?)]}")
            if cleaned and cleaned not in cleaned_urls:
                cleaned_urls.append(cleaned)
        return cleaned_urls

    def fetch_url(self, url: str, max_chars: int = 3500) -> str:
        """
        Tải nội dung từ một URL, làm sạch mã HTML và trả về văn bản súc tích.
        Kết quả được lưu vào bộ nhớ đệm Redis theo TTL.
        """
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return f"Đường dẫn không hợp lệ (URL phải bắt đầu bằng http:// hoặc https://): {url}"

        # 1. Kiểm tra cache từ Redis / In-Memory
        cached_content = self._get_cached(url)
        if cached_content is not None:
            return cached_content

        # 2. Gửi request lấy HTML từ web
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

        # 3.1 Nếu là trang membership của Rentzy, bổ sung thông tin 4 gói từ API backend được render bằng React
        if "rentzy.vn/member-ship" in url:
            pkg_info = self._fetch_rentzy_membership_api()
            if pkg_info:
                text = f"{pkg_info}\n\n[Quy định & Chính sách gói]:\n{text}"

        if not text:
            text = f"Đã kết nối thành công tới {url} nhưng trang web không có nội dung văn bản hiển thị."

        # 4. Lưu vào bộ nhớ đệm Redis
        self._set_cached(url, text)
        return text

    def _fetch_rentzy_membership_api(self) -> str:
        """
        Gọi trực tiếp API backend của Rentzy (https://api.rentzy.vn/v1/consumer-membership-package/list)
        để lấy đầy đủ thông số 4 gói thành viên thời gian thực (DC2990K, DC3990K, DC6990K, DC9990K)
        vốn được tải động qua React/Gatsby trên trình duyệt.
        """
        api_url = "https://api.rentzy.vn/v1/consumer-membership-package/list"
        try:
            headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(api_url, headers=headers)
            if res.status_code == 200:
                data = res.json().get("data", [])
                lines = ["[Các gói thành viên hiển thị trên Website Rentzy]:"]
                # Sắp xếp theo giá tăng dần
                data = sorted(data, key=lambda x: x.get("price", 0))
                for item in data:
                    name = item.get("name", "")
                    price = item.get("price", 0)
                    months = item.get("packageTimeMonth", 24)
                    voucher = item.get("voucherAmount", 0)
                    contents = [c for c in item.get("contents", []) if c]
                    first_order = item.get("maxFirstOrderValue")

                    price_str = f"{price:,.0f} đ".replace(",", ".")
                    voucher_str = f"{voucher:,.0f} đ".replace(",", ".") if voucher else ""

                    line = f"- Gói {name}: Giá {price_str} ({months} tháng)"
                    if contents:
                        line += f"\n  + Ưu đãi: {'; '.join(contents)}"
                    if voucher:
                        line += f"\n  + Voucher tặng kèm: {voucher_str}"
                    if first_order:
                        first_order_str = f"{first_order:,.0f} đ".replace(",", ".")
                        line += f"\n  + Hạn mức đơn đầu: {first_order_str}"
                    lines.append(line)
                return "\n".join(lines)
        except Exception as exc:
            logger.warning("  └── [WebReader] Không thể tải dữ liệu API membership (%s): %s", api_url, exc)
        return ""

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
        """Xoá toàn bộ bộ nhớ cache trên Redis và In-Memory."""
        if self._redis_client:
            try:
                keys = self._redis_client.keys("rentzy:web_cache:*")
                if keys:
                    self._redis_client.delete(*keys)
                logger.info("  └── [WebReader:Redis] Đã xoá toàn bộ Redis web cache (%d keys)", len(keys) if keys else 0)
            except Exception as exc:
                logger.warning("  └── [WebReader:Redis] Lỗi khi xoá Redis web cache: %s", exc)
        self._memory_cache.clear()


web_reader_service = WebReaderService()

