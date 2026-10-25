"""系统公告接口（公开）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.announcement import AnnouncementOut
from app.services import admin_service

router = APIRouter(prefix="/announcements", tags=["公告"])


@router.get("", response_model=list[AnnouncementOut], summary="生效中的系统公告")
def active_announcements(db: Session = Depends(get_db)):
    return admin_service.list_announcements(db, only_active=True)["items"]
