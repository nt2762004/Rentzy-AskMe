from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    record_id: Optional[str] = Field(default=None, description="Mã bản ghi nghiệp vụ (VD: ASKME-012)")
    sub_topic: Optional[str] = Field(default=None, description="Chủ đề con / Sub-intent (VD: huy_coc_doi_mau)")
    question: Optional[str] = Field(default=None, description="Câu hỏi mẫu của người dùng")
    answer: Optional[str] = Field(default=None, description="Câu trả lời chính thức")
    status: Literal["active", "inactive"] = Field(default="active", description="Trạng thái hiệu lực của bài viết")
    topic: str = Field(..., description="Chủ đề chính (VD: Chính sách, Gói thành viên, Quy trình, Dịch vụ)")
    source_url: str = Field(..., description="URL nguồn chính thức của bài viết")
    updated_at: str = Field(..., description="Ngày cập nhật (định dạng YYYY-MM-DD)")
    approver: str = Field(..., description="Người phê duyệt nội dung (VD: Business Lead, Legal Team)")
    version: str = Field(default="1.0", description="Phiên bản tài liệu")

class DocumentBase(BaseModel):
    title: str = Field(..., description="Tiêu đề tài liệu sạch (không chứa mã ID thừa)")
    content: str = Field(..., description="Nội dung bài viết dùng cho Vector Search & RAG")
    metadata: DocumentMetadata

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[Literal["active", "inactive"]] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    record_id: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    source_url: Optional[str] = None
    updated_at: Optional[str] = None
    approver: Optional[str] = None
    version: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    metadata: DocumentMetadata
    created_at: datetime
    updated_at_dt: datetime

    model_config = ConfigDict(from_attributes=True)

class ChunkMetadata(DocumentMetadata):
    document_id: str
    chunk_index: int

class SearchFilter(BaseModel):
    status: Optional[Literal["active", "inactive"]] = Field(default="active", description="Mặc định chỉ tìm bài active")
    record_id: Optional[str] = Field(default=None, description="Lọc chính xác theo Mã nghiệp vụ (VD: ASKME-012)")
    topic: Optional[str] = Field(default=None, description="Lọc theo chủ đề")
    sub_topic: Optional[str] = Field(default=None, description="Lọc theo chủ đề con")
    approver: Optional[str] = Field(default=None, description="Lọc theo người phê duyệt")
    version: Optional[str] = Field(default=None, description="Lọc theo phiên bản")
    source_url: Optional[str] = Field(default=None, description="Lọc theo URL nguồn")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Câu hỏi hoặc từ khóa tìm kiếm")
    top_k: int = Field(default=5, ge=1, le=50, description="Số lượng chunk trả về")
    filter: Optional[SearchFilter] = Field(default_factory=SearchFilter, description="Bộ lọc đa metadata")

class SearchResultItem(BaseModel):
    chunk_id: str
    question: Optional[str] = Field(default=None, description="Câu hỏi trích xuất riêng")
    answer: Optional[str] = Field(default=None, description="Câu trả lời trích xuất riêng")
    content: str = Field(..., description="Nội dung đầy đủ dùng làm Context cho LLM")
    score: float
    metadata: ChunkMetadata

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]

