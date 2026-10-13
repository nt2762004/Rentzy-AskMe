from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="Vai trò: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Nội dung tin nhắn")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Thời gian gửi tin nhắn")

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Mã định danh phiên làm việc (Session UUID)")
    message: str = Field(..., description="Tin nhắn/câu hỏi của người dùng")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Mã định danh phiên làm việc")
    intent: str = Field(..., description="Mã Intent nhận diện được (1 trong 14 mã)")
    intent_title: str = Field(..., description="Tên tiếng Việt hiển thị của Intent")
    confidence: float = Field(..., description="Độ tin cậy nhận diện Intent (0.00 -> 1.00)")
    reply_message: str = Field(..., description="Câu trả lời phản hồi cho khách hàng")
    need_clarification: bool = Field(default=False, description="True nếu chatbot cần hỏi lại để làm rõ ý định")
    suggest_sales: bool = Field(default=False, description="True nếu đề xuất chuyển sang nhân viên Sales")
    suggested_options: Optional[List[str]] = Field(default=None, description="Danh sách gợi ý chọn lựa khi cần làm rõ nhu cầu")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Trích dẫn các bài viết nguồn từ Story 1 nếu có")
    handled_by: Optional[str] = Field(default=None, description="Tên Agent hoặc Sub-agent chịu trách nhiệm xử lý yêu cầu")

class SessionState(BaseModel):
    session_id: str
    messages: List[ChatMessage] = []
    fallback_count: int = 0
    current_intent: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
