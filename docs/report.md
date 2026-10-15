# BÁO CÁO TỔNG KẾT KẾT QUẢ THỰC HIỆN CÔNG VIỆC
**Dự án:** Rentzy - Trợ lý Thời trang AI AskMe  
**Giai đoạn:** Nâng cấp Multi-Agent & Tối ưu hóa hệ thống

---

## I. TỔNG QUAN CÔNG VIỆC ĐÃ LÀM

1. **Tái cấu trúc kiến trúc từ Single Agent sang Multi-Agent Supervisor:**
   - Phân tách luồng xử lý thành các Sub-Agent độc lập: `MembershipAgent`, `OverviewAgent`, `SupportAgent`, `PolicyAgent`, `CatalogAgent`.
   - Xây dựng Supervisor điều phối trung tâm bằng LangGraph StateGraph.
   - Chuẩn hóa hệ thống logging theo cấu trúc cây điều phối trực quan.

2. **Năng lực tra cứu Web động & Agentic Tool Calling:**
   - Xây dựng module `WebReader` tự động cào và chuyển đổi nội dung web sang Markdown sạch.
   - Tích hợp tool `fetch_web_page` cho `MembershipAgent` qua Gemini Automatic Function Calling (AFC).

3. **Caching dữ liệu tra cứu Web trên Redis:**
   - Lưu trữ cache kết quả cào web trực tiếp trên Redis (`rentzy:web_cache:*`).
   - Cấu hình TTL tự động hết hạn sau 1 giờ (3600s).
   - Tích hợp cơ chế In-Memory fallback an toàn khi Redis gặp sự cố.

4. **Thiết lập Guardrail ngăn bot tự ý đưa Hotline & Địa chỉ Showroom:**
   - Cấu hình prompt và bộ lọc hậu xử lý (post-processing).
   - Bot chỉ cung cấp hotline/showroom khi khách hàng chủ động yêu cầu hoặc hỏi địa chỉ.

5. **Xây dựng cơ chế Fast Reply cho câu chào hỏi đơn giản:**
   - Nhận diện tức thì các câu chào thuần túy (*"hello"*, *"hi"*, *"xin chào"*, *"chào shop"*...).
   - Phản hồi ngay lập tức (< 5ms, Zero LLM call, tiết kiệm 100% token) kèm 4 gợi ý thao tác nhanh.

6. **Khử lặp câu chào "Chào Nàng" trong phiên hội thoại đa lượt:**
   - Nhận biết lượt hội thoại qua biến `is_first_turn` từ lịch sử phiên chat trên Redis.
   - Áp dụng chỉ thị prompt và bộ lọc regex tự động cắt bỏ lời chào dư thừa từ lượt chat thứ 2 trở đi.

7. **Tinh chỉnh từ đệm tiếng Việt & Bộ lọc từ khóa tránh phân loại sai:**
   - Bổ sung các trợ từ chào hỏi tự nhiên: *"nhá"*, *"nhen"*, *"nè"*, *"nà"*, *"nhaaa"*...
   - Loại bỏ từ khóa *"shop"* đứng đơn lẻ để tránh nhầm câu chào thành hỏi địa chỉ showroom.

---

## II. CÔNG NGHỆ SỬ DỤNG

- **Kiến trúc điều phối hội thoại:** `LangGraph` (`StateGraph`, `Supervisor Multi-Agent Pattern`)
- **Mô hình ngôn ngữ lớn (LLM):** `Google Gemini 3.1 Flash Lite` (`google-genai` SDK)
- **Cơ chế gọi công cụ (Tool Calling):** Gemini Automatic Function Calling (AFC)
- **Lưu trữ phiên & Bộ nhớ đệm:** `Redis` (Session Checkpointer, Web Cache TTL 1h)
- **Web Scraping & HTTP Client:** `BeautifulSoup4`, `httpx`
- **Backend Framework:** `FastAPI`, `Pydantic v2`, `Uvicorn`
- **Testing Framework:** `Pytest`, `pytest-asyncio`

---