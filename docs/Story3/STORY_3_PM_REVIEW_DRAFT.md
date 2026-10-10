# Story 3 PM Review Draft: Xây Dựng Giao Diện AskMe AI Chatbot Widget & Menu Bắt Đầu

## 1. Tóm Tắt Kết Quả Hoàn Thành (Summary of Completed Tasks)

| Hạng mục Task | Trạng thái | Chi tiết triển khai |
| :--- | :--- | :--- |
| **Giao diện Chatbot Widget** | ✅ Hoàn thành | Thiết kế dạng Floating Launcher Button + Chat Drawer Popover theo tông màu thương hiệu Rentzy (Rose Pink `#E05263`, Dark Charcoal `#1A1817`, Nude Cream `#FAF6F0`). Responsive 100% trên cả Mobile & Desktop. |
| **Phương thức Tích hợp 1 Dòng Code** | ✅ Hoàn thành | Tích hợp cực kỳ đơn giản qua 1 thẻ `<script src="/static/js/rentzy-widget.js"></script>`. Tương thích mọi nền tảng (Haravan, Sapo, WordPress, HTML/JS, React). |
| **Menu Đề Xuất Bắt Đầu (7 Quick Chips)** | ✅ Hoàn thành | Hiển thị 7 tùy chọn nhanh phổ biến nhất MVP: Tìm hiểu Rentzy, Tìm sản phẩm, Hướng dẫn thuê, Chính sách cọc/trả đồ, Sản phẩm thanh lý, Gói thành viên, Kết nối tư vấn viên. |
| **Hỗ trợ Nhập Câu Hỏi Tự Nhiên** | ✅ Hoàn thành | Ô nhập tin nhắn hỗ trợ gõ phím Enter/nút Gửi, kết nối trực tiếp API `POST /api/v1/chat` của FastAPI Backend. |
| **Hỗ trợ Nút Lựa Chọn Nhanh (Pills)** | ✅ Hoàn thành | Render các nút gợi ý `suggested_options` khi hệ thống kích hoạt `need_clarification = true`. |
| **Hiển thị Liên Kết & Product Card** | ✅ Hoàn thành | Render thẻ sản phẩm sang trọng (ảnh, giá thuê, nút đặt đồ), trích dẫn nguồn Knowledge Base và Banner chuyển đổi Sales Zalo 24/7 khi `suggest_sales = true`. |
| **Lưu Context Session ID** | ✅ Hoàn thành | Tự động sinh và lưu giữ `session_id` trong `localStorage` để duy trì lịch sử hội thoại khi khách chuyển trang. |
| **Kiểm thử Tự động & Accessibility** | ✅ Hoàn thành | 33/33 Pytest unit/integration test suite vượt qua 100% (bao gồm 4 test suite UI tại `tests/test_story3_ui.py`). |

---

## 2. Hình Ảnh Minh Họa Giao Diện & Test Case

Giao diện thực tế đã kiểm thử bằng Browser Subagent tại `http://localhost:8000/`:

- **Trang chủ E-commerce Demo Rentzy**: Tích hợp sẵn Script Widget ở góc dưới cùng bên phải.
- **Floating Button & Badge**: Màu Rose Pink kiêu sa, biểu tượng AI badge nhấp nháy thu hút sự chú ý.
- **Cửa sổ Chat Popover**: Tiêu đề "Rentzy Advisor", 7 nút Quick Action Chip và khung nhập liệu mượt mà.

---

## 3. Hướng Dẫn Nghiệm Thu Dành Cho PM / Client

1. Khởi động server FastAPI:
   ```cmd
   .\run_server.bat
   ```
2. Mở trình duyệt web truy cập trang demo:
   [http://localhost:8000/](http://localhost:8000/)
3. Bấm nút Chatbot AI góc phải dưới màn hình.
4. Bấm thử các nút trong Menu Bắt Đầu hoặc tự gõ câu hỏi:
   - *"Rentzy có chính sách cọc đồ thế nào?"*
   - *"Gói thành viên membership có quyền lợi gì?"*
   - *"Dịch thuật bài báo này giúp tôi"* (Kiểm tra phản hồi Fallback lịch sự).
