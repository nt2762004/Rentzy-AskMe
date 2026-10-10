# Story 1 Summary — Xây dựng và quản lý kho kiến thức Rentzy

## 1. Mục tiêu

Xây dựng một kho kiến thức chính thức cho AI-Powered AskMe để chatbot chỉ sử dụng nội dung đã được Rentzy phê duyệt khi trả lời khách hàng.

Story 1 tập trung vào việc thu thập, chuẩn hóa, quản lý và chuẩn bị nội dung Rentzy để AI có thể tìm kiếm và truy xuất; đồng thời hỗ trợ cập nhật nội dung khi nguồn Website/CMS thay đổi.

## 2. Phạm vi

### 2.1. Nguồn nội dung

Nguồn chính trong Story 1 là Website/CMS của Rentzy, bao gồm:

- Giới thiệu Rentzy
- Dịch vụ
- Gói thành viên
- Quy trình
- Chính sách

Cần xác định danh sách nguồn nội dung và nguồn dữ liệu chính thức cho từng nhóm nội dung.

### 2.2. Xử lý và chuẩn hóa nội dung

- Thu thập các nội dung cần thiết.
- Loại bỏ nội dung trùng lặp.
- Xác định và loại bỏ nội dung hết hiệu lực.
- Phân loại nội dung theo chủ đề.
- Xác định nguồn chính thức cho từng chủ đề.
- Chuẩn bị dữ liệu để AI có thể tìm kiếm và truy xuất.

### 2.3. Metadata

Mỗi nội dung cần có các thông tin:

- Chủ đề
- URL nguồn
- Ngày cập nhật
- Người phê duyệt
- Phiên bản
- Trạng thái hiệu lực

Các thông tin này cần hỗ trợ việc xác định nguồn, thời điểm cập nhật và trạng thái sử dụng của nội dung.

### 2.4. Cập nhật và phê duyệt

Cần có quy trình để:

- Cập nhật nội dung.
- Quản lý phiên bản.
- Xác định nội dung đang có hiệu lực.
- Xác định nội dung hết hiệu lực.
- Xác định người chịu trách nhiệm phê duyệt từng nhóm nội dung.
- Cho phép Business cập nhật nội dung mà không cần sửa prompt hoặc source code.

### 2.5. Đồng bộ với CMS

Khi CMS thay đổi, hệ thống cần có cơ chế để cập nhật lại kho kiến thức tương ứng.

Phần này phụ thuộc vào thông tin/API/access thực tế mà Rentzy cung cấp.

## 3. Các phase thực hiện

### Phase 1 — Requirement & Data Preparation

- Nhận và review data từ Rentzy.
- Xác định các nguồn Website/CMS.
- Thu thập nội dung cần thiết.
- Kiểm tra chất lượng dữ liệu.
- Xác định nội dung trùng lặp hoặc hết hiệu lực.
- Làm rõ các thông tin còn thiếu trước khi triển khai.

**Output:**
- Bộ dữ liệu đầu vào đã được xác định.
- Danh sách nguồn nội dung.
- Các dependency/thông tin cần Rentzy bổ sung.

### Phase 2 — Knowledge Base Design

- Chuẩn hóa cấu trúc nội dung.
- Phân loại nội dung theo topic.
- Xác định source chính thức.
- Chuẩn bị metadata cho từng content.
- Xác định cách quản lý version và trạng thái hiệu lực.
- Xác định quy trình cập nhật/phê duyệt.

**Output:**
- Cấu trúc Knowledge Base.
- Quy ước metadata.
- Quy tắc quản lý trạng thái và phiên bản.

### Phase 3 — AI Retrieval / Knowledge Integration

- Chuẩn bị dữ liệu cho AI search/retrieval.
- Đưa nội dung vào hệ thống tìm kiếm/truy xuất.
- Kiểm tra khả năng tìm đúng nội dung liên quan.
- Kiểm tra câu trả lời dựa trên nội dung Rentzy được phê duyệt.

**Output:**
- Knowledge Base có thể được AI sử dụng để tìm kiếm và truy xuất.
- Bộ kiểm thử ban đầu cho việc truy xuất nội dung.

### Phase 4 — Content Lifecycle & CMS Sync

- Quản lý nội dung active/inactive.
- Xử lý version và nội dung hết hiệu lực.
- Xác định cách phát hiện thay đổi từ CMS.
- Đồng bộ nội dung thay đổi.
- Cập nhật lại dữ liệu phục vụ AI retrieval khi content thay đổi.
- Đảm bảo Business có thể cập nhật content mà không cần chỉnh sửa prompt/source code.

**Output:**
- Quy trình cập nhật nội dung.
- Cơ chế đồng bộ khi CMS thay đổi.
- Knowledge Base phản ánh nội dung hiện hành.

### Phase 5 — Testing & Validation

- Kiểm tra chatbot chỉ sử dụng nguồn Rentzy đã được phê duyệt.
- Kiểm tra URL nguồn và ngày cập nhật.
- Kiểm tra nội dung hết hiệu lực không được sử dụng.
- Kiểm tra việc cập nhật nội dung.
- Kiểm tra quá trình đồng bộ khi CMS thay đổi.
- Review và validation với Business/Rentzy.

**Output:**
- Kết quả kiểm thử.
- Danh sách issue cần xử lý.
- Story đạt các Acceptance Criteria sau khi được Business/Rentzy xác nhận.

## 4. Acceptance Criteria

Story 1 được xem là đạt khi:

- Mỗi câu trả lời sử dụng nguồn Rentzy đã được phê duyệt.
- Mỗi nội dung có URL nguồn và ngày cập nhật.
- Nội dung hết hiệu lực không được sử dụng.
- Business có thể cập nhật nội dung mà không cần sửa prompt hoặc source code.
- Có người chịu trách nhiệm phê duyệt từng nhóm nội dung.

## 5. Dependency / Thông tin cần từ Rentzy

Trước hoặc trong quá trình triển khai cần có:

- Data/content chính thức.
- Danh sách nguồn Website/CMS.
- URL tương ứng.
- Thông tin về ngày cập nhật, version, trạng thái hiệu lực và người phê duyệt nếu đã có.
- Quy tắc xác định content hết hiệu lực nếu Rentzy đã có.
- Thông tin/API/access của CMS nếu CMS sync nằm trong scope triển khai.

## 6. Ranh giới của Story 1

Story 1 tập trung vào **Knowledge Base và việc quản lý nội dung phục vụ AI**.

Các phần như intent recognition, chatbot UI, product search từ ERP, product recommendation, Sales handoff và analytics thuộc các Story khác trong Use Case 1 và không được coi là phạm vi chính của Story 1.

## 7. Hướng lập kế hoạch

Kế hoạch coding nên được xây dựng sau khi đã review đầy đủ data và thông tin từ Rentzy.

Các phase ở trên cần được breakdown thành các task cụ thể. Mỗi task cần xác định:

- Mục tiêu
- Input/dependency
- Kết quả cần đạt
- Điều kiện hoàn thành
- Thời gian implement dự kiến

Chi tiết kỹ thuật chưa được đưa vào file này; technical implementation plan sẽ được xác định ở bước planning tiếp theo.
