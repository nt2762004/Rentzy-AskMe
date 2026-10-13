from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.session import session_service
from app.graph.dialogue_graph import dialogue_graph
from app.core.intents import INTENT_CATALOG
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["AskMe Conversation AI"])

@router.post("", summary="Gửi tin nhắn hội thoại với AskMe AI (LangGraph + Gemini Flash Lite)", response_model=ChatResponse)
def chat_with_askme(req: ChatRequest):
    """
    API tiếp nhận câu hỏi hội thoại tự nhiên của khách hàng:
    - Lưu và duy trì lịch sử phiên chat theo `session_id` qua Redis.
    - Nhận diện 14 Intent (hỗ trợ lỗi chính tả, từ viết tắt 'cọc', 'tly', 'sm'...).
    - Điều hướng hỏi làm rõ nhu cầu hoặc đề xuất chuyển Sales sau 2 lần không nhận diện được.
    - Trả về câu trả lời tự nhiên kèm danh sách trích dẫn nguồn từ Story 1.
    """
    try:
        # 1. Ghi tin nhắn user vào Session Store
        session_service.add_message(req.session_id, role="user", content=req.message)

        # 2. Chạy LangGraph StateGraph Execution
        state_input = {
            "session_id": req.session_id,
            "message": req.message
        }
        
        graph_output = dialogue_graph.invoke(state_input)

        intent_code = graph_output.get("intent", "out_of_scope")
        intent_info = INTENT_CATALOG.get(intent_code, {})
        intent_title = intent_info.get("title", "Khác")
        reply = graph_output.get("reply_message", "Rentzy xin chào Nàng! Nàng cần hỗ trợ gì ạ?")

        # 3. Ghi tin nhắn assistant vào Session Store và cập nhật current_intent
        session_service.add_message(req.session_id, role="assistant", content=reply, intent=intent_code)

        handled_by = graph_output.get("handled_by", "supervisor")
        logger.info(
            "[Supervisor:Outbound] Hoàn tất | Handled By: [%s] | Reply Length: %d chars\n"
            "============================================================",
            handled_by,
            len(reply),
        )

        return ChatResponse(
            session_id=req.session_id,
            intent=intent_code,
            intent_title=intent_title,
            confidence=round(float(graph_output.get("confidence", 1.0)), 2),
            reply_message=reply,
            need_clarification=bool(graph_output.get("need_clarification", False)),
            suggest_sales=bool(graph_output.get("suggest_sales", False)),
            suggested_options=graph_output.get("suggested_options"),
            sources=graph_output.get("sources"),
            handled_by=handled_by,
        )

    except Exception as e:
        logger.error(f"Lỗi khi xử lý hội thoại chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý hệ thống AskMe: {str(e)}"
        )
