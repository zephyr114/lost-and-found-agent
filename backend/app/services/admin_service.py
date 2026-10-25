"""管理服务：统计、审核、用户管理、举报处理、公告、日志。"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents import matching
from app.models.agent_log import AgentLog
from app.models.announcement import Announcement
from app.models.claim import Claim
from app.models.item import Item
from app.models.match import Match
from app.models.operation_log import OperationLog
from app.models.report import Report
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from app.services import message_service


def log_operation(db: Session, admin: User, action: str, target_type: str, target_id: int | None = None, detail: dict | None = None) -> None:
    db.add(
        OperationLog(
            admin_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )
    db.commit()


# ---------- 统计 ----------

def get_statistics(db: Session) -> dict:
    return {
        "users_total": db.query(User).count(),
        "users_active": db.query(User).filter(User.status == "active").count(),
        "users_disabled": db.query(User).filter(User.status == "disabled").count(),
        "items_total": db.query(Item).count(),
        "items_lost": db.query(Item).filter(Item.item_type == "lost").count(),
        "items_found": db.query(Item).filter(Item.item_type == "found").count(),
        "items_pending_audit": db.query(Item).filter(Item.audit_status == "pending").count(),
        "items_claimed": db.query(Item).filter(Item.status == "claimed").count(),
        "claims_total": db.query(Claim).count(),
        "claims_pending": db.query(Claim).filter(Claim.status == "pending").count(),
        "matches_total": db.query(Match).count(),
        "reports_pending": db.query(Report).filter(Report.status == "pending").count(),
        "announcements_active": db.query(Announcement).filter(Announcement.status == "active").count(),
    }


# ---------- 物品审核 ----------

def list_pending_items(db: Session, skip: int = 0, limit: int = 20) -> dict:
    query = db.query(Item).filter(Item.audit_status == "pending")
    total = query.count()
    items = query.order_by(Item.created_at.asc()).offset(skip).limit(limit).all()
    user_ids = {it.user_id for it in items}
    names = dict(db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()) if user_ids else {}
    return {
        "items": [
            {
                "id": it.id,
                "item_type": it.item_type,
                "title": it.title,
                "category": it.category,
                "location": it.location,
                "description": it.description,
                "images": it.images or [],
                "event_time": it.event_time.isoformat(),
                "created_at": it.created_at.isoformat(),
                "username": names.get(it.user_id),
            }
            for it in items
        ],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


def audit_item(db: Session, item: Item, decision: str, comment: str | None, admin: User) -> Item:
    """审核物品：通过后公开可见并触发智能匹配；结果通知发布者。"""
    if item.audit_status == "approved" and decision == "approve":
        raise HTTPException(status_code=400, detail="该物品已通过审核")
    item.audit_status = "approved" if decision == "approve" else "rejected"
    db.commit()
    log_operation(
        db, admin, f"item_{decision}", "item", item.id,
        {"title": item.title, "comment": comment},
    )
    if decision == "approve":
        # 审核通过后运行智能匹配
        matching.background_matching(item.id, item.user_id)
        message_service.create_message(
            db, item.user_id,
            f"您发布的「{item.title}」已通过审核，现已公开展示，并已运行智能匹配。",
            message_type="audit",
        )
    else:
        message_service.create_message(
            db, item.user_id,
            f"您发布的「{item.title}」未通过审核。原因：{comment or '信息不完整或不符合规范'}。修改后可重新提交审核。",
            message_type="audit",
        )
    db.refresh(item)
    return item


# ---------- 用户管理 ----------

def set_user_status(db: Session, target: User, status: str, admin: User) -> User:
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能操作自己的账号")
    if target.role == "admin" and status == "disabled":
        raise HTTPException(status_code=400, detail="不能禁用管理员账号")
    target.status = status
    db.commit()
    log_operation(db, admin, f"user_{status}", "user", target.id, {"username": target.username})
    message_service.create_message(
        db, target.id,
        "您的账号已被禁用，请联系管理员。" if status == "disabled" else "您的账号已恢复正常使用。",
        message_type="system",
    )
    db.refresh(target)
    return target


# ---------- 认领管理 ----------

def list_all_claims(db: Session, skip: int = 0, limit: int = 20) -> dict:
    query = db.query(Claim)
    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
    from app.services.claim_service import serialize_claim

    return {
        "items": [serialize_claim(db, c) for c in claims],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


# ---------- 举报 ----------

def create_report(db: Session, reporter: User, target_type: str, target_id: int, reason: str, description: str | None) -> Report:
    from app.models.claim import Claim as ClaimModel

    if target_type == "item" and db.get(Item, target_id) is None:
        raise HTTPException(status_code=404, detail="被举报的物品不存在")
    if target_type == "user" and db.get(User, target_id) is None:
        raise HTTPException(status_code=404, detail="被举报的用户不存在")
    if target_type == "claim" and db.get(ClaimModel, target_id) is None:
        raise HTTPException(status_code=404, detail="被举报的申请不存在")

    report = Report(
        reporter_id=reporter.id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def serialize_report(report: Report, reporter_name: str | None = None) -> dict:
    return {
        "id": report.id,
        "reporter_id": report.reporter_id,
        "reporter_name": reporter_name,
        "target_type": report.target_type,
        "target_id": report.target_id,
        "reason": report.reason,
        "description": report.description,
        "status": report.status,
        "handler_id": report.handler_id,
        "handler_comment": report.handler_comment,
        "created_at": report.created_at,
    }


def list_reports(db: Session, skip: int = 0, limit: int = 20, status: str | None = None) -> dict:
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    ids = {r.reporter_id for r in reports}
    names = dict(db.query(User.id, User.username).filter(User.id.in_(ids)).all()) if ids else {}
    return {
        "items": [serialize_report(r, names.get(r.reporter_id)) for r in reports],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


def handle_report(db: Session, report: Report, action: str, comment: str | None, admin: User) -> Report:
    if report.status != "pending":
        raise HTTPException(status_code=400, detail="该举报已处理")
    report.status = "handled" if action == "handled" else "dismissed"
    report.handler_id = admin.id
    report.handler_comment = comment
    db.commit()
    log_operation(db, admin, f"report_{action}", "report", report.id, {"reason": report.reason})
    message_service.create_message(
        db, report.reporter_id,
        f"您提交的举报（{report.reason}）已处理：{(comment or ('已核实处理' if action == 'handled' else '经核实不成立'))}。感谢您的监督。",
        message_type="report",
    )
    db.refresh(report)
    return report


# ---------- 公告 ----------

def create_announcement(db: Session, data: AnnouncementCreate, admin: User) -> Announcement:
    ann = Announcement(title=data.title.strip(), content=data.content, status="active", created_by=admin.id)
    db.add(ann)
    db.commit()
    db.refresh(ann)
    log_operation(db, admin, "announcement_create", "announcement", ann.id, {"title": ann.title})
    return ann


def update_announcement(db: Session, ann: Announcement, data: AnnouncementUpdate, admin: User) -> Announcement:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(ann, key, value)
    db.commit()
    db.refresh(ann)
    log_operation(db, admin, "announcement_update", "announcement", ann.id, updates)
    return ann


def delete_announcement(db: Session, ann: Announcement, admin: User) -> None:
    db.delete(ann)
    db.commit()
    log_operation(db, admin, "announcement_delete", "announcement", ann.id, {"title": ann.title})


def list_announcements(db: Session, only_active: bool = True, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(Announcement)
    if only_active:
        query = query.filter(Announcement.status == "active")
    total = query.count()
    items = query.order_by(Announcement.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "status": a.status,
                "created_by": a.created_by,
                "created_at": a.created_at,
                "updated_at": a.updated_at,
            }
            for a in items
        ],
        "total": total,
    }


# ---------- 日志 ----------

def list_agent_logs(db: Session, skip: int = 0, limit: int = 50, task_type: str | None = None) -> dict:
    query = db.query(AgentLog)
    if task_type:
        query = query.filter(AgentLog.task_type == task_type)
    total = query.count()
    rows = query.order_by(AgentLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "task_type": r.task_type,
                "tool_name": r.tool_name,
                "input_data": r.input_data,
                "tool_result": r.tool_result,
                "execution_time_ms": r.execution_time_ms,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


def list_operation_logs(db: Session, skip: int = 0, limit: int = 50) -> dict:
    query = db.query(OperationLog)
    total = query.count()
    rows = query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
    ids = {r.admin_id for r in rows}
    names = dict(db.query(User.id, User.username).filter(User.id.in_(ids)).all()) if ids else {}
    return {
        "items": [
            {
                "id": r.id,
                "admin_id": r.admin_id,
                "admin_name": names.get(r.admin_id),
                "action": r.action,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "detail": r.detail,
                "created_at": r.created_at,
            }
            for r in rows
        ],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }
