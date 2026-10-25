"""健康检查接口。"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health_check(db: Session = Depends(get_db)) -> dict:
    """检查服务与数据库是否正常（数据库异常时返回 degraded 而非 500）。"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {type(exc).__name__}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "database": db_status,
        "time": datetime.now(timezone.utc).isoformat(),
    }
