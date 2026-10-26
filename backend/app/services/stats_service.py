"""公开统计数据服务：首页数据看板使用（不包含敏感信息）。"""

from sqlalchemy.orm import Session

from app.models.claim import Claim
from app.models.item import Item
from app.models.match import Match
from app.models.user import User


def get_public_statistics(db: Session) -> dict:
    """返回可公开展示的聚合数据。"""
    approved = Item.audit_status == "approved"
    return {
        "items_total": db.query(Item).filter(approved).count(),
        "items_lost": db.query(Item).filter(approved, Item.item_type == "lost").count(),
        "items_found": db.query(Item).filter(approved, Item.item_type == "found").count(),
        "items_claimed": db.query(Item).filter(approved, Item.status == "claimed").count(),
        "claims_total": db.query(Claim).count(),
        "matches_total": db.query(Match).count(),
        "matches_confirmed": db.query(Match).filter(Match.status == "confirmed").count(),
        "users_total": db.query(User).filter(User.status == "active").count(),
    }
