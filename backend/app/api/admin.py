"""管理接口：统计、信息审核、用户管理、认领管理、举报处理、公告管理、日志。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.database.session import get_db
from app.models.announcement import Announcement
from app.models.item import Item
from app.models.report import Report
from app.models.user import User
from app.schemas.admin import AuditItemRequest, StatisticsOut, UserStatusRequest
from app.schemas.announcement import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate
from app.schemas.report import HandleReportRequest
from app.services import admin_service, item_service

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/statistics", response_model=StatisticsOut, summary="数据统计面板")
def statistics(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return admin_service.get_statistics(db)


# ---------- 信息审核 ----------


@router.get("/items/pending", summary="待审核物品列表")
def pending_items(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_pending_items(db, skip=(page - 1) * size, limit=size)


@router.put("/items/{item_id}/audit", summary="审核物品（通过 / 拒绝）")
def audit_item(
    item_id: int,
    data: AuditItemRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    item = admin_service.audit_item(db, item, data.decision, data.comment, admin)
    return {"message": "审核完成", "item_id": item.id, "audit_status": item.audit_status}


@router.delete("/items/{item_id}", summary="删除违规物品")
def admin_delete_item(
    item_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    title = item.title
    item_service.delete_item(db, item)
    admin_service.log_operation(db, admin, "item_delete", "item", item_id, {"title": title})
    return {"message": "已删除违规物品"}


# ---------- 用户管理 ----------


@router.get("/users", summary="用户列表")
def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    from app.services.user_service import list_users as _list_users

    users = _list_users(db, skip=(page - 1) * size, limit=size)
    total = db.query(User).count()
    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "avatar": u.avatar,
                "credit_score": u.credit_score,
                "role": u.role,
                "status": u.status,
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.put("/users/{user_id}/status", summary="禁用 / 启用用户")
def set_user_status(
    user_id: int,
    data: UserStatusRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    admin_service.set_user_status(db, target, data.status, admin)
    return {"message": "操作成功", "user_id": target.id, "status": target.status}


# ---------- 认领申请管理 ----------


@router.get("/claims", summary="全部认领申请")
def all_claims(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_all_claims(db, skip=(page - 1) * size, limit=size)


# ---------- 举报处理 ----------


@router.get("/reports", summary="举报列表")
def list_reports(
    status: str | None = Query(default=None, pattern="^(pending|handled|dismissed)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_reports(db, skip=(page - 1) * size, limit=size, status=status)


@router.put("/reports/{report_id}/handle", summary="处理举报")
def handle_report(
    report_id: int,
    data: HandleReportRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="举报不存在")
    report = admin_service.handle_report(db, report, data.action, data.comment, admin)
    return admin_service.serialize_report(report, None)


# ---------- 公告管理 ----------


@router.get("/announcements", response_model=list[AnnouncementOut], summary="全部公告（管理端）")
def admin_announcements(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return admin_service.list_announcements(db, only_active=False)["items"]


@router.post("/announcements", response_model=AnnouncementOut, status_code=201, summary="发布公告")
def create_announcement(
    data: AnnouncementCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.create_announcement(db, data, admin)


@router.put("/announcements/{ann_id}", response_model=AnnouncementOut, summary="编辑公告")
def update_announcement(
    ann_id: int,
    data: AnnouncementUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ann = db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    return admin_service.update_announcement(db, ann, data, admin)


@router.delete("/announcements/{ann_id}", summary="删除公告")
def delete_announcement(
    ann_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ann = db.get(Announcement, ann_id)
    if ann is None:
        raise HTTPException(status_code=404, detail="公告不存在")
    admin_service.delete_announcement(db, ann, admin)
    return {"message": "已删除"}


# ---------- 日志 ----------


@router.get("/agent-logs", summary="Agent 运行日志")
def agent_logs(
    task_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_agent_logs(db, skip=(page - 1) * size, limit=size, task_type=task_type)


@router.get("/operation-logs", summary="操作审计日志")
def operation_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return admin_service.list_operation_logs(db, skip=(page - 1) * size, limit=size)
