"""公开统计接口：数据看板用。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview", summary="公开数据概览（数据看板）")
def overview(db: Session = Depends(get_db)):
    return stats_service.get_public_statistics(db)
