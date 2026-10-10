from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "api_version": settings.API_V1_STR,
        "python_version": "3.12"
    }
