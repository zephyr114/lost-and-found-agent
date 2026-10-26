"""智能匹配接口：运行分析、查看推荐、匹配详情。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents import matching
from app.api.deps import get_current_user, get_current_user_optional
from app.database.session import get_db
from app.models.item import Item
from app.models.match import Match
from app.models.user import User
from app.schemas.match import AnalyzeRequest, MatchListResponse, MatchOut
from app.services import item_service, message_service

router = APIRouter(prefix="/matches", tags=["智能匹配"])


def _check_item_visible(item: Item, viewer: User | None) -> None:
    if item.audit_status != "approved" and (
        viewer is None or (viewer.id != item.user_id and viewer.role != "admin")
    ):
        raise HTTPException(status_code=404, detail="物品不存在或尚未通过审核")


def _single_match_dict(db: Session, m: Match) -> dict:
    items = dict(db.query(Item.id, Item.title).filter(Item.id.in_([m.lost_item_id, m.found_item_id])).all())
    return {
        "id": m.id,
        "lost_item_id": m.lost_item_id,
        "found_item_id": m.found_item_id,
        "match_score": m.match_score,
        "match_reason": m.match_reason or [],
        "status": m.status,
        "created_at": m.created_at,
        "lost_title": items.get(m.lost_item_id),
        "found_title": items.get(m.found_item_id),
    }


@router.post("/analyze", response_model=MatchListResponse, summary="运行匹配分析（发布者或管理员）")
def analyze(data: AnalyzeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = item_service.get_item_or_404(db, data.item_id)
    if item.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只能分析自己发布的物品")
    results = matching.run_matching_pipeline(db, item.id, user_id=user.id, notify=True)
    return {"items": results, "total": len(results)}


@router.get("/recommendations", response_model=MatchListResponse, summary="查看物品的匹配推荐")
def recommendations(
    item_id: int = Query(...),
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    _check_item_visible(item, viewer)

    # 已有匹配记录直接返回
    if item.item_type == "lost":
        rows = db.query(Match).filter(Match.lost_item_id == item.id).order_by(Match.match_score.desc()).limit(10).all()
    else:
        rows = db.query(Match).filter(Match.found_item_id == item.id).order_by(Match.match_score.desc()).limit(10).all()
    if rows:
        return {"items": matching.serialize_matches(db, rows), "total": len(rows)}

    # 否则现场计算（不持久化、不通知）
    scored = matching.search_similar_items(db, item, limit=10)
    titles = dict(db.query(Item.id, Item.title).filter(Item.id.in_([c.id for c, _ in scored])).all()) if scored else {}
    result = []
    for cand, res in scored:
        if res["score"] < matching.MATCH_THRESHOLD:
            continue
        result.append(
            {
                "id": 0,
                "lost_item_id": item.id if item.item_type == "lost" else cand.id,
                "found_item_id": cand.id if item.item_type == "lost" else item.id,
                "match_score": res["score"],
                "match_reason": res["reasons"],
                "status": "live",
                "created_at": item.created_at,
                "lost_title": titles.get(item.id if item.item_type == "lost" else cand.id),
                "found_title": titles.get(cand.id if item.item_type == "lost" else item.id),
            }
        )
    return {"items": result, "total": len(result)}


@router.get("/{match_id}", response_model=MatchOut, summary="匹配详情")
def get_match(
    match_id: int,
    viewer: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    m = db.get(Match, match_id)
    if m is None:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    lost = db.get(Item, m.lost_item_id)
    found = db.get(Item, m.found_item_id)
    involved = viewer is not None and (viewer.role == "admin" or viewer.id in {lost.user_id, found.user_id})
    if not involved:
        if not (lost and found and lost.audit_status == "approved" and found.audit_status == "approved"):
            raise HTTPException(status_code=404, detail="匹配记录不存在")
    return _single_match_dict(db, m)


@router.post("/{match_id}/confirm", response_model=MatchOut, summary="确认匹配（失主标记「这是我的物品」）")
def confirm_match(
    match_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """仅失物发布者可以确认匹配；确认后通知招领发布者尽快联系。"""
    m = db.get(Match, match_id)
    if m is None:
        raise HTTPException(status_code=404, detail="匹配记录不存在")
    lost = db.get(Item, m.lost_item_id)
    found = db.get(Item, m.found_item_id)
    if lost is None or found is None:
        raise HTTPException(status_code=404, detail="匹配关联的物品不存在")
    if lost.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="只有失主可以确认匹配")

    if m.status != "confirmed":
        m.status = "confirmed"
        db.commit()
        message_service.create_message(
            db,
            found.user_id,
            f"失主已确认「{lost.title}」与您发布的「{found.title}」匹配成功（匹配度 {m.match_score}），请及时联系失主完成交接。",
            message_type="match",
        )
        db.refresh(m)
    return _single_match_dict(db, m)
