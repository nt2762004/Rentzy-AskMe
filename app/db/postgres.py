from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.document import Base
from typing import Generator
import logging

import os

logger = logging.getLogger(__name__)

# Thử kết nối PostgreSQL; nếu Postgres chưa bật Docker sẽ tự động fallback sang SQLite local
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info("Kết nối thành công PostgreSQL!")
except Exception as e:
    logger.warning(f"Không thể kết nối PostgreSQL ({e}). Tự động fallback sang SQLite local!")
    os.makedirs("db", exist_ok=True)
    sqlite_url = "sqlite:///./db/rentzy_kb.db"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import inspect

def init_postgres_db() -> None:
    """Khởi tạo bảng trong Database (Postgres hoặc SQLite fallback) nếu chưa tồn tại."""
    try:
        inspector = inspect(engine)
        if inspector.has_table("documents"):
            columns = [col["name"] for col in inspector.get_columns("documents")]
            if "record_id" not in columns:
                logger.info("Phát hiện Schema mới (thêm record_id/sub_topic/question/answer), tự động cập nhật bảng...")
                Base.metadata.drop_all(bind=engine)
    except Exception as e:
        logger.warning(f"Check schema warning: {e}")
    Base.metadata.create_all(bind=engine)

# Auto-ensure tables exist on module load
try:
    init_postgres_db()
except Exception as e:
    logger.warning(f"Auto init db warning: {e}")



def get_db() -> Generator[Session, None, None]:
    """Dependency lấy DB Session cho FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
