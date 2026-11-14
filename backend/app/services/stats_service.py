"""公开统计数据服务：首页数据看板使用（不包含敏感信息）。"""

from sqlalchemy import func
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
    rows = (
        db.query(Item.location, Item.item_type, func.count(Item.id))
        .filter(approved)
        .group_by(Item.location, Item.item_type)
        .all()
    )
    agg: dict[str, dict] = {}
    for name, item_type, count in rows:
        entry = agg.setdefault(name, {"name": name, "lost": 0, "found": 0, "total": 0})
        entry["lost" if item_type == "lost" else "found"] += count
        entry["total"] += count
    top_locations = sorted(agg.values(), key=lambda e: e["total"], reverse=True)[:6]

    return {
        "items_total": db.query(Item).filter(approved).count(),
        "top_locations": top_locations,
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
