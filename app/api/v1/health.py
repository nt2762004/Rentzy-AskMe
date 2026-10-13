from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", tags=["Health"], operation_id="health_check")
@router.head("/health", tags=["Health"], include_in_schema=False)
def health_check():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "api_version": settings.API_V1_STR,
        "python_version": "3.12"
    }
