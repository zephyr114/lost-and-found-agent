"""数据库引擎与会话管理（SQLAlchemy 2.x）。

通过环境变量 DATABASE_URL 切换数据库：
- 默认：sqlite:///./lost_found.db（开发环境开箱即用）
- MySQL：mysql+pymysql://user:pass@host:3306/lost_found?charset=utf8mb4
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _resolve_database_url(url: str) -> str:
    """规范化连接串：相对 SQLite 锚定到 backend 目录；PostgreSQL 驱动补全。"""
    # Render 等平台注入的连接串为 postgres://，补全为 psycopg3 驱动
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite:///./"):
        backend_dir = Path(__file__).resolve().parent.parent.parent
        db_path = backend_dir / url.removeprefix("sqlite:///./")
        return f"sqlite:///{db_path.as_posix()}"
    return url


database_url = _resolve_database_url(settings.database_url)
is_sqlite = database_url.startswith("sqlite")

engine_kwargs: dict = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类（第二阶段起添加 User / Item 等模型）。"""


def get_db():
    """FastAPI 依赖：提供数据库会话并在请求结束后关闭。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
