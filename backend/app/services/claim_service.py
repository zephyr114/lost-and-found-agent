"""认领业务服务：申请、处理、状态流转与通知。"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.item import Item
from app.models.user import User
from app.services import message_service


def get_claim_or_404(db: Session, claim_id: int) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="认领申请不存在")
    return claim


def serialize_claim(db: Session, claim: Claim) -> dict:
    applicant = db.get(User, claim.applicant_id)
    item = db.get(Item, claim.item_id)
    return {
        "id": claim.id,
        "item_id": claim.item_id,
        "applicant_id": claim.applicant_id,
        "applicant_name": applicant.username if applicant else None,
        "proof_description": claim.proof_description,
        "proof_images": claim.proof_images or [],
        "contact": claim.contact,
        "status": claim.status,
        "review_comment": claim.review_comment,
        "created_at": claim.created_at,
        "updated_at": claim.updated_at,
        "item_title": item.title if item else None,
        "item_type": item.item_type if item else None,
    }


def create_claim(
    db: Session,
    item: Item,
    applicant: User,
    proof_description: str,
    contact: str | None,
    proof_images: list[str],
) -> Claim:
    """提交认领申请：仅招领物品、非本人发布、已审核且仍可认领。"""
    if item.item_type != "found":
        raise HTTPException(status_code=400, detail="只有招领物品可以申请认领")
    if item.user_id == applicant.id:
        raise HTTPException(status_code=400, detail="不能认领自己发布的物品")
    if item.audit_status != "approved":
        raise HTTPException(status_code=400, detail="该物品尚未通过审核")
    if item.status != "active":
        raise HTTPException(status_code=400, detail="该物品已被认领或关闭")

    existing = (
        db.query(Claim)
        .filter(Claim.item_id == item.id, Claim.applicant_id == applicant.id, Claim.status == "pending")
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="你已提交过该物品的认领申请，请等待处理")

    claim = Claim(
        item_id=item.id,
        applicant_id=applicant.id,
        proof_description=proof_description,
        proof_images=proof_images or [],
        contact=contact,
        status="pending",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    # 通知物品发布者
    message_service.create_message(
        db,
        item.user_id,
        f"用户「{applicant.username}」对您发布的招领物品「{item.title}」提交了认领申请，请及时处理（申请编号 {claim.id}）。",
        message_type="claim",
        sender_id=applicant.id,
    )
    return claim


def list_my_claims(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> dict:
    """我提交的认领申请。"""
    query = db.query(Claim).filter(Claim.applicant_id == user_id)
    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "items": [serialize_claim(db, c) for c in claims],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


def list_received_claims(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> dict:
    """收到我发布的物品的认领申请。"""
    query = db.query(Claim).join(Item, Claim.item_id == Item.id).filter(Item.user_id == user_id)
    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "items": [serialize_claim(db, c) for c in claims],
        "total": total,
        "page": skip // limit + 1 if limit else 1,
        "size": limit,
    }


def approve_claim(db: Session, claim: Claim, owner: User, comment: str | None) -> Claim:
    """同意认领：物品标记为已认领，其余待处理申请自动拒绝。"""
    item = db.get(Item, claim.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.user_id != owner.id:
        raise HTTPException(status_code=403, detail="只有物品发布者可以处理认领申请")
    if claim.status != "pending":
        raise HTTPException(status_code=400, detail=f"该申请已处理（当前状态 {claim.status}）")

    claim.status = "approved"
    claim.review_comment = comment
    item.status = "claimed"

    # 自动拒绝同一物品的其他待处理申请
    others = (
        db.query(Claim)
        .filter(Claim.item_id == item.id, Claim.status == "pending", Claim.id != claim.id)
        .all()
    )
    for other in others:
        other.status = "rejected"
        other.review_comment = "该物品已被他人成功认领"
        message_service.create_message(
            db,
            other.applicant_id,
            f"很抱歉，您申请的物品「{item.title}」已被他人成功认领。",
            message_type="claim",
        )
    db.commit()

    applicant = db.get(User, claim.applicant_id)
    message_service.create_message(
        db,
        claim.applicant_id,
        f"恭喜！您对「{item.title}」的认领申请已通过。请与发布者「{owner.username}」联系交接物品。",
        message_type="claim",
        sender_id=owner.id,
    )
    db.refresh(claim)
    return claim


def reject_claim(db: Session, claim: Claim, owner: User, comment: str | None) -> Claim:
    item = db.get(Item, claim.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.user_id != owner.id:
        raise HTTPException(status_code=403, detail="只有物品发布者可以处理认领申请")
    if claim.status != "pending":
        raise HTTPException(status_code=400, detail=f"该申请已处理（当前状态 {claim.status}）")

    claim.status = "rejected"
    claim.review_comment = comment
    db.commit()
    message_service.create_message(
        db,
        claim.applicant_id,
        f"很抱歉，您对「{item.title}」的认领申请未通过。"
        + (f"原因：{comment}" if comment else "您可以补充更多证明后重新申请。"),
        message_type="claim",
        sender_id=owner.id,
    )
    db.refresh(claim)
    return claim


def request_proof(db: Session, claim: Claim, owner: User, comment: str | None) -> Claim:
    """要求补充证明。"""
    item = db.get(Item, claim.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    if item.user_id != owner.id:
        raise HTTPException(status_code=403, detail="只有物品发布者可以处理认领申请")
    if claim.status != "pending":
        raise HTTPException(status_code=400, detail=f"该申请已处理（当前状态 {claim.status}）")

    claim.status = "need_more_proof"
    claim.review_comment = comment or "请补充物品特征或购买凭证等证明"
    db.commit()
    message_service.create_message(
        db,
        claim.applicant_id,
        f"您对「{item.title}」的认领申请需要补充证明：{claim.review_comment}",
        message_type="claim",
        sender_id=owner.id,
    )
    db.refresh(claim)
    return claim


def cancel_claim(db: Session, claim: Claim, applicant: User) -> Claim:
    """申请人撤回待处理的申请。"""
    if claim.applicant_id != applicant.id:
        raise HTTPException(status_code=403, detail="无权操作该申请")
    if claim.status not in ("pending", "need_more_proof"):
        raise HTTPException(status_code=400, detail="该申请已处理，无法撤回")
    claim.status = "cancelled"
    db.commit()
    db.refresh(claim)
    return claim


def add_proof_images(db: Session, claim: Claim, applicant: User, urls: list[str]) -> Claim:
    """申请人对 need_more_proof 的申请补充证明图片并重新提交。"""
    if claim.applicant_id != applicant.id:
        raise HTTPException(status_code=403, detail="无权操作该申请")
    claim.proof_images = (claim.proof_images or []) + urls
    claim.status = "pending"
    db.commit()
    item = db.get(Item, claim.item_id)
    if item:
        message_service.create_message(
            db,
            item.user_id,
            f"用户「{applicant.username}」已补充「{item.title}」认领申请的证明材料，请重新审核（申请编号 {claim.id}）。",
            message_type="claim",
            sender_id=applicant.id,
        )
    db.refresh(claim)
    return claim
