import logging
import sys

# Đảm bảo UTF-8 trên Windows console (tránh lỗi charmap/UnicodeEncodeError với tiếng Việt & emoji)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Cấu hình logging hiển thị trực tiếp ra Terminal (chỉ giữ log Agent, ẩn log HTTP của thư viện thứ 3)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logging.getLogger("app").setLevel(logging.INFO)

# Ẩn hoàn toàn log HTTP và warning từ các thư viện ngoài
import warnings
warnings.filterwarnings("ignore")

for noisy in [
    "httpx",
    "httpcore",
    "google_genai",
    "google.genai",
    "google_genai.models",
    "google",
    "sqlalchemy.engine",
    "urllib3",
    "asyncio",
    "uvicorn.access",
]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.chat import router as chat_router
from app.db.postgres import init_postgres_db
from app.db.qdrant import init_qdrant_collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo Postgres & Qdrant Cloud khi ứng dụng khởi động
    try:
        init_postgres_db()
        init_qdrant_collection()
    except Exception as e:
        print(f"[Lifespan Warning] Khởi tạo DB/Qdrant: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(knowledge_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", operation_id="get_root_page")
@app.head("/", include_in_schema=False)
def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
