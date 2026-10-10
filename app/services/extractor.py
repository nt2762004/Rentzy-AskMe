import pandas as pd
from typing import List, Dict, Any
from app.schemas.knowledge import DocumentCreate, DocumentMetadata

class ExcelDataExtractor:
    def __init__(self, excel_path: str = "docs/Rentzy_AskMe_AI_Training_Data.xlsx"):
        self.excel_path = excel_path

    def extract_documents(self) -> List[DocumentCreate]:
        """Đọc và trích xuất dữ liệu từ các sheet của file Excel thành các đối tượng DocumentCreate sạch."""
        documents = []
        xl = pd.ExcelFile(self.excel_path)
        
        # 1. Trích xuất dữ liệu từ sheet "Training Data"
        if "Training Data" in xl.sheet_names:
            df = xl.parse("Training Data")
            for idx, row in df.iterrows():
                record_id = str(row.get("Record ID", f"REC-{idx+1}")).strip()
                intent = str(row.get("Intent", "Chung")).strip() if pd.notna(row.get("Intent")) else "Chung"
                sub_intent = str(row.get("Sub-intent", "")).strip() if pd.notna(row.get("Sub-intent")) else ""
                user_q = str(row.get("User utterance", "")).strip() if pd.notna(row.get("User utterance")) else ""
                answer = str(row.get("Canonical answer", "")).strip() if pd.notna(row.get("Canonical answer")) else ""
                target_url = str(row.get("Target URL", "https://rentzy.vn")).strip() if pd.notna(row.get("Target URL")) else "https://rentzy.vn"
                
                if not answer or answer == "nan":
                    continue

                # Tiêu đề sạch thuần túy (không dính mã RECORD_ID)
                clean_title = intent
                if sub_intent and sub_intent != "nan":
                    clean_title += f" - {sub_intent}"
                
                # Tạo nội dung sạch (Clean Content) dùng cho LLM Context
                content_parts = []
                if user_q and user_q != "nan":
                    content_parts.append(f"Câu hỏi: {user_q}")
                content_parts.append(f"Trả lời: {answer}")
                clean_content = "\n".join(content_parts)

                # Gán metadata chuẩn với các trường đã được tách bạch
                metadata = DocumentMetadata(
                    record_id=record_id if record_id != "nan" else None,
                    sub_topic=sub_intent if sub_intent != "nan" else None,
                    question=user_q if user_q != "nan" else None,
                    answer=answer if answer != "nan" else None,
                    status="active",
                    topic=intent,
                    source_url=target_url if target_url.startswith("http") else "https://rentzy.vn",
                    updated_at="2026-10-01",
                    approver="Rentzy Business Team",
                    version="1.0"
                )

                documents.append(DocumentCreate(
                    title=clean_title,
                    content=clean_content,
                    metadata=metadata
                ))

        return documents

excel_extractor = ExcelDataExtractor()
