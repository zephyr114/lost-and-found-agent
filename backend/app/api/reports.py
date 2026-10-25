"""用户侧接口：提交举报、查看我的举报。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportListResponse, ReportOut
from app.services import admin_service

router = APIRouter(prefix="/reports", tags=["举报"])


@router.post("", response_model=ReportOut, status_code=201, summary="提交举报")
def create_report(data: ReportCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = admin_service.create_report(db, user, data.target_type, data.target_id, data.reason, data.description)
    return admin_service.serialize_report(report, user.username)


@router.get("/my", response_model=ReportListResponse, summary="我的举报")
def my_reports(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    query = db.query(Report).filter(Report.reporter_id == user.id)
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(size).all()
    return {
        "items": [admin_service.serialize_report(r, user.username) for r in reports],
        "total": total,
        "page": page,
        "size": size,
    }
