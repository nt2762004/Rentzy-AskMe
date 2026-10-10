# Story 3: Plan Xây Dựng Widget Chatbot AskMe & Menu Bắt Đầu

## 1. Tổng Quan Kiến Trúc Widget (Single-Script Embed)

Widget được thiết kế theo phương thức **Single-Script Embed Snippet** chuẩn công nghiệp (tương tự Intercom, Crisp, Tawk.to). Đối tác hoặc đội ngũ làm Web của Rentzy chỉ cần chèn **1 dòng code JS** vào website (Haravan, Sapo, WordPress, HTML/JS custom, React...):

```html
<!-- Rentzy AskMe AI Chatbot Widget -->
<script src="http://localhost:8000/static/js/rentzy-widget.js" defer></script>
```

Tệp Script này sẽ tự động:
1. Tải CSS giao diện tinh tế, sang trọng (`static/css/rentzy-widget.css`).
2. Khởi tạo nút **Floating Launcher Button** ở góc dưới cùng bên phải màn hình (Mobile & Desktop).
3. Tạo cửa sổ chat **Chat Drawer / Popover** hoạt động mượt mà.
4. Quản lý `session_id` trong `localStorage` để giữ context hội thoại khi khách chuyển trang.
5. Gọi trực tiếp API Backend FastAPI: `POST /api/v1/chat`.

---

## 2. Các Thành Phần Giao Diện & Tính Năng Chính

### A. Nút Launcher & Badge
- Floating Button màu Rose Pink (`#E05263`) bóng bẩy, biểu tượng Chat Bot & hiệu ứng Pulse micro-animation.
- Unread Badge / Thông báo chào mừng nhỏ nhấp nháy khi khách mới vào trang.

### B. Header Giao Diện Chat
- Avatar AI Assistant ("Rentzy Advisor").
- Trạng thái "Trực tuyến" (Online indicator dot).
- Nút thu nhỏ / đóng cửa sổ.

### C. Menu Đề Xuất Bắt Đầu (7 Quick Action Chips)
Khách mới chưa biết hỏi gì có thể bấm ngay 1 trong 7 tùy chọn phổ biến:
1. 🌸 **Tìm hiểu về Rentzy** (`rentzy_overview`)
2. 👗 **Tìm sản phẩm** (`product_search`)
3. 🏷️ **Hướng dẫn thuê đồ** (`rental_pricing`)
4. 📜 **Chính sách thuê và trả đồ** (`deposit_policy`)
5. 🛍️ **Sản phẩm thanh lý** (`liquidation`)
6. 💎 **Gói thành viên** (`membership`)
7. 👩‍💼 **Kết nối nhân viên tư vấn** (`contact_support`)

### D. Khung Trợ Giúp Nhanh & Rich Components
- **Quick Reply Pills (`suggested_options`)**: Khi `need_clarification = true`, hiển thị danh sách các nút gợi ý làm rõ ý định.
- **Product Card / Rental Card**: Khi Intent liên quan đến xem sản phẩm hoặc bảng giá, hiển thị thẻ sản phẩm mượt mà kèm ảnh, giá thuê, nút hành động.
- **Sales Escalation Banner (`suggest_sales = true`)**: Khi phát hiện khách cần tư vấn sâu, hiển thị Banner kết nối Zalo / Hotline Nhân viên tư vấn trực tiếp.
- **Sources & Citations**: Nguồn trích dẫn chính sách từ Knowledge Base.

---

## 3. Danh Sách Nhiệm Vụ Kỹ Thuật (Tasks)

- [x] **Task 1**: Lập kế hoạch chi tiết Story 3 (`docs/Story3/STORY_3_PLANNING.md`).
- [ ] **Task 2**: Viết Style CSS hệ thống Rentzy Widget (`static/css/rentzy-widget.css`) đáp ứng Responsive Mobile & Desktop, Glassmorphism, Nude/Rose Gold tone.
- [ ] **Task 3**: Viết JS Widget Core Engine (`static/js/rentzy-widget.js`) xử lý DOM Injection, Event Listener, `session_id` LocalStorage, và gọi Backend `POST /api/v1/chat`.
- [ ] **Task 4**: Tạo Landing Page Demo E-Commerce Rentzy (`static/index.html`) minh họa việc tích hợp Widget lên trang chủ.
- [ ] **Task 5**: Cập nhật FastAPI App (`app/main.py`) để mount static files & phục vụ demo UI tại route `/`.
- [ ] **Task 6**: Viết Pytest test suite cho UI & Static assets (`tests/test_story3_ui.py`).
- [ ] **Task 7**: Tạo kịch bản Test Demo Story 3 (`docs/Story3/DEMO_STORY_3.txt`) và Báo cáo PM Review (`docs/Story3/STORY_3_PM_REVIEW_DRAFT.md`).
