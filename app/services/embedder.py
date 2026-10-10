from google import genai
from app.core.config import settings
from typing import List, Optional

class EmbeddingService:
    def __init__(self, model_name: str = None, api_key: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            key = (self.api_key or settings.GEMINI_API_KEY or "").strip()
            if not key:
                raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env")
            self._client = genai.Client(api_key=key)
        return self._client

    def generate_embedding(self, text: str) -> List[float]:
        """Tạo vector embedding cho 1 đoạn văn bản bằng Google GenAI SDK."""
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        return response.embeddings[0].values

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Tạo vector embedding cho danh sách các đoạn văn bản theo batch."""
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=texts
        )
        return [emb.values for emb in response.embeddings]

embedding_service = EmbeddingService()
