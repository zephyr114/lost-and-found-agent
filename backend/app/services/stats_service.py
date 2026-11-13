"""公开统计数据服务：首页数据看板使用（不包含敏感信息）。"""

from sqlalchemy.orm import Session, aliased

from app.models.claim import Claim
from app.models.item import Item
from app.models.match import Match
from app.models.user import User


def get_public_statistics(db: Session) -> dict:
    """返回可公开展示的聚合数据（匹配仅统计双方都已审核通过的物品）。"""
    approved = Item.audit_status == "approved"
    lost_item = aliased(Item)
    found_item = aliased(Item)
    approved_matches = (
        db.query(Match)
        .join(lost_item, lost_item.id == Match.lost_item_id)
        .join(found_item, found_item.id == Match.found_item_id)
        .filter(lost_item.audit_status == "approved", found_item.audit_status == "approved")
    )
    return {
        "items_total": db.query(Item).filter(approved).count(),
        "items_lost": db.query(Item).filter(approved, Item.item_type == "lost").count(),
        "items_found": db.query(Item).filter(approved, Item.item_type == "found").count(),
        "items_claimed": db.query(Item).filter(approved, Item.status == "claimed").count(),
        "items_resolved": db.query(Item).filter(approved, Item.status == "resolved").count(),
        "claims_total": db.query(Claim).count(),
        "matches_total": approved_matches.count(),
        "matches_confirmed": approved_matches.filter(Match.status == "confirmed").count(),
        "matches_handed_over": approved_matches.filter(Match.status == "handed_over").count(),
        "users_total": db.query(User).filter(User.status == "active").count(),
    }
