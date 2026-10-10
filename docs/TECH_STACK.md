# 🛠️ Gợi ý Tech Stack & Hạ tầng Cloud — Story 1: Knowledge Base & AI Agent (Python Core)

## 1. Mô hình Kiến trúc Tổng quan (RAG Architecture)

Dự án áp dụng mô hình **RAG (Retrieval-Augmented Generation) chuẩn sản xuất**, sử dụng **Python** làm ngôn ngữ chính với khả năng **Metadata Filtering** để lọc nội dung active/inactive và cơ chế **Sync tự động với CMS**.

```
                           ┌───────────────────────────┐
                           │   Rentzy Website / CMS    │
                           └─────────────┬─────────────┘
                                         │ (Webhook / Cron Job)
                                         ▼
                           ┌───────────────────────────┐
                           │  Python Ingestion Engine  │
                           │    (Crawl4AI + FastAPI)   │
                           └─────────────┬─────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
 ┌───────────────────────────────────┐       ┌───────────────────────────────────┐
 │   Relational DB (Supabase/Postgres)│       │      Vector DB (Qdrant Cloud)    │
 │ ─────────────┬─────────────────── │       │ ─────────────┬─────────────────── │
 │ - Metadata (Topic, Approver)      │       │ - Text Embeddings                │
 │ - Document Versions & History     │       │ - Payload (Status, URL, Updated) │
 │ - Active/Inactive Flags           │       │ - Fast Similarity Search         │
 └───────────────────────────────────┘       └───────────────────────────────────┘
                                                           ▲
                                                           │ (Hybrid Vector Search)
                                                           │
┌──────────────────────────┐                     ┌───────────────────────────┐
│        User Query        │ ──────────────────► │  Python AI Retrieval Engine│
└──────────────────────────┘                     │  (LlamaIndex + FastAPI)   │
                                                 └─────────────┬─────────────┘
                                                               │ (Augmented Prompt)
                                                               ▼
                                                 ┌───────────────────────────┐
                                                 │   LLM (Gemini / OpenAI)   │
                                                 └─────────────┬─────────────┘
                                                               │
                                                               ▼
                                                 [Response + Source Citation URL]
```

---

## 2. Chi tiết Thành phần Tech Stack Đề xuất

### 2.1. Core Framework & RAG Engine (Python)
- **FastAPI (v0.110+)**: Web Framework hiệu năng cao, viết RESTful API kết nối Chatbot UI và nhận Webhook từ CMS.
- **LlamaIndex (Python)**: *Khuyên dùng hàng đầu cho Knowledge Base RAG*.
  - *Lý do chọn:* Hỗ trợ sẵn các Data Connectors, Node Parsers (Chunking theo Markdown/Header), Metadata Extraction và Metadata Filtering linh hoạt.
- **LangChain / LangGraph**: Có thể kết hợp nếu sau này nâng cấp hệ thống lên Multi-Agent (Sales Agent + Customer Support Agent ở các Story tiếp theo).

### 2.2. Vector Database (Lưu trữ Vector & Lọc Metadata)
- **Qdrant (Qdrant Cloud / Self-hosted Docker)**: *Lựa chọn tối ưu nhất*.
  - *Lý do chọn:* Viết bằng Rust cho tốc độ cực nhanh, hỗ trợ **Payload Filtering** mạnh mẽ (cho phép lọc `status == "active"`, `version == "1.2"`, `topic == "policy"` trực tiếp khi search Vector). Bản Cloud hỗ trợ Free Tier 1GB.
- **pgvector (PostgreSQL Extension trên Supabase)**:
  - *Lý do chọn:* Nếu muốn hợp nhất cả Relational Data (Metadata) và Vector Embeddings vào đúng 1 Database duy nhất để dễ quản lý.
- **Pinecone**: Dịch vụ Vector DB Serverless fully managed, dễ sử dụng cho giai đoạn MVP.

### 2.3. Embedding Model & LLM Provider
- **Embedding Model:**
  - **Google `text-embedding-004`** hoặc **OpenAI `text-embedding-3-small`**: Chi phí thấp, hỗ trợ đa ngôn ngữ tốt (Đặc biệt là Tiếng Việt).
  - *(Self-hosted/Free)*: `sentence-transformers/multilingual-e5-base` hoặc `bge-m3` nếu muốn chạy offline hoàn toàn.
- **Generative LLM:**
  - **Google Gemini 2.5 Flash / 1.5 Flash**: Tốc độ xử lý siêu nhanh, context window lớn, chi phí API cực kỳ tiết kiệm.
  - **OpenAI GPT-4o-mini**: Rất mạnh trong việc tuân thủ cấu trúc JSON output và trích dẫn URL chính xác.

### 2.4. Data Ingestion, Scraping & Chunking
- **Crawl4AI (Python)**: Thư viện cào dữ liệu tối ưu riêng cho AI, tự động chuyển đổi các trang HTML của Rentzy thành dạng Markdown sạch.
- **Unstructured / LangChain Text Splitters**: Dùng `MarkdownNodeParser` hoặc `RecursiveCharacterTextSplitter` cắt nhỏ bài viết theo tiêu đề (`#`, `##`) giữ nguyên ngữ cảnh.

### 2.5. Metadata & Business Admin Store
- **Supabase (PostgreSQL Cloud)**:
  - Cung cấp sẵn giao diện Admin UI trực quan để đội ngũ Business dễ dàng chỉnh sửa thông tin metadata, đổi trạng thái `active/inactive` hoặc phê duyệt nội dung.
  - Tích hợp sẵn Webhooks để tự động gửi thông báo sang FastAPI Backend khi nội dung được duyệt.

---

## 3. Hạ tầng Cloud & Hosting Đề xuất (Production-Ready & Tiết kiệm)

| Thành phần | Dịch vụ Cloud đề xuất | Chi phí & Ghi chú |
| :--- | :--- | :--- |
| **Python FastAPI Backend** | **GCP Cloud Run** / **Render.com** / **Railway** | Triển khai dạng Docker Container, Auto-scale, tính phí theo lượng request. |
| **Vector Database** | **Qdrant Cloud** | Gói Free Tier 1GB (Đủ chứa ~50.000 chunks bài viết). |
| **Metadata DB & Admin UI** | **Supabase Cloud** | Gói Free Tier (500MB Database, đủ quản lý toàn bộ bài viết & metadata). |
| **Task Queue / CMS Sync** | **Celery + Redis** hoặc **APScheduler** | Xử lý cào dữ liệu và tính toán Embedding ở background không gây block API. |

---

## 4. Giải pháp Kỹ thuật cho các Yêu cầu Đặc thù Story 1

### 4.1. Lọc Nội dung Active / Inactive
Trong Qdrant Vector DB, lưu trữ cấu trúc Payload kèm theo từng Vector:
```json
{
  "content": "Chính sách đổi trả gói dịch vụ áp dụng trong vòng 7 ngày...",
  "metadata": {
    "topic": "policy",
    "source_url": "https://rentzy.vn/policy/refund",
    "updated_at": "2026-09-24",
    "version": "2.0",
    "approver": "Business Lead",
    "status": "active"
  }
}
```
Khi thực hiện Vector Search từ LlamaIndex, áp dụng bộ lọc:
```python
from qdrant_client.http import models

qdrant_filter = models.Filter(
    must=[
        models.FieldCondition(
            key="status",
            match=models.MatchValue(value="active")
        )
    ]
)
```

### 4.2. Cơ chế Đồng bộ CMS (CMS Sync Engine)
1. **Trường hợp CMS có Webhook:** Khi bài viết được xuất bản/chỉnh sửa trên CMS -> CMS bắn Webhook tới endpoint `POST /api/v1/cms-webhook` của FastAPI.
2. **Trường hợp CMS không có Webhook:** Đặt lịch Cron Job (APScheduler/Celery) chạy định kỳ (ví dụ 1 lần/ngày) gọi `Crawl4AI` kiểm tra danh sách URL và so sánh sitemap để cập nhật những trang có thay đổi.

### 4.3. Prompt Engineering cho Trích dẫn Nguồn
```text
System Prompt:
Bạn là trợ lý AI chính thức của Rentzy. Hãy sử dụng DUY NHẤT các đoạn thông tin được cung cấp dưới đây để trả lời câu hỏi của người dùng.

Yêu cầu nghiêm ngặt:
1. Không tự bịa thêm thông tin ngoài tài liệu được cung cấp.
2. Với mỗi thông tin được đưa ra, phải trích dẫn rõ nguồn theo định dạng: 
   Nguồn: [Tên bài viết](URL) - Cập nhật ngày: YYYY-MM-DD.
3. Nếu tài liệu không đề cập, hãy lịch sự trả lời rằng bạn chưa có thông tin về vấn đề này.
```

---

## 🎯 5. Bộ Tech Stack Chốt Triển khai (Recommended Final Stack)

```bash
Backend Engine : Python 3.11+ | FastAPI | Uvicorn
RAG Framework  : LlamaIndex Python
Vector DB      : Qdrant (Payload Filtering enabled)
Relational DB  : PostgreSQL (Supabase Cloud)
Crawler        : Crawl4AI + BeautifulSoup4
LLM & Embed    : Gemini 2.5 Flash / OpenAI text-embedding-3-small
Hosting        : Docker Container on GCP Cloud Run / Render
```
