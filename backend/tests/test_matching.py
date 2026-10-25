"""第五阶段验收测试：智能匹配 Agent。"""

import uuid

from app.agents import matching
from app.models.agent_log import AgentLog
from app.models.item import Item
from app.models.match import Match


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client, username=None):
    r = client.post(
        "/api/auth/register",
        json={
            "username": username or uniq("u"),
            "email": f"{uniq('e')}@example.com",
            "password": "secret123",
        },
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def publish_item(client, token, item_type, title, **overrides):
    payload = {
        "item_type": item_type,
        "title": title,
        "category": "电子数码",
        "color": "黑色",
        "brand": "苹果",
        "location": "图书馆",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "description": "外观完好，有轻微划痕",
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    r = client.post("/api/items", json=payload, headers=auth(token))
    assert r.status_code == 201
    return r.json()


def approve_item(item_id: int):
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        item = db.get(Item, item_id)
        if item:
            item.audit_status = "approved"
            db.commit()
    finally:
        db.close()


def run_pipeline(item_id: int, user_id: int | None = None):
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        return matching.run_matching_pipeline(db, item_id, user_id=user_id, notify=True)
    finally:
        db.close()


# ---------- 属性提取 ----------


def test_extract_item_attributes_rules():
    attrs = matching.extract_item_attributes("我在图书馆丢失了一个黑色苹果手机，外面有透明壳")
    assert attrs["color"] == "黑色"
    assert attrs["brand"] == "苹果"
    assert attrs["category"] == "电子数码"
    assert attrs["location"] == "图书馆"


def test_extract_item_attributes_no_llm_key():
    from app.core.config import settings

    assert settings.llm_api_key == ""  # 测试环境未配置 LLM，走规则引擎


# ---------- 匹配打分 ----------


def _make_item(item_type="lost", **overrides):
    from datetime import datetime

    from app.database.session import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)  # 确保表存在（该文件可能独立运行）

    db = SessionLocal()
    try:
        base = dict(
            user_id=1,
            item_type=item_type,
            title="黑色苹果手机",
            category="电子数码",
            description="外观完好，有轻微划痕",
            color="黑色",
            brand="苹果",
            location="图书馆",
            latitude=31.2304,
            longitude=121.4737,
            event_time=datetime(2026, 10, 20, 10, 0, 0),
            images=[],
            status="active",
            audit_status="approved",
        )
        base.update(overrides)
        item = Item(**base)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    finally:
        db.close()


def test_calculate_match_score_high():
    lost = _make_item("lost")
    found = _make_item("found", title="捡到一部黑色苹果手机")
    result = matching.calculate_match_score(lost, found)
    assert result["score"] >= 60
    assert "物品类别一致" in result["reasons"]
    assert "颜色描述一致" in result["reasons"]
    assert "品牌一致" in result["reasons"]


def test_calculate_match_score_low():
    lost = _make_item("lost")
    found = _make_item(
        "found",
        title="捡到一把雨伞",
        category="雨伞水杯",
        color="红色",
        brand=None,
        description="九成新",
        latitude=39.9,
        longitude=116.4,
    )
    result = matching.calculate_match_score(lost, found)
    assert result["score"] < matching.MATCH_THRESHOLD


def test_location_distance():
    km = matching.query_location_distance(31.2304, 121.4737, 39.9087, 116.3975)
    assert km is not None and km > 900  # 上海到北京约 1067km


def test_submit_audit_task_risky():
    result = matching.submit_audit_task("捡到钱包，请加微信转账 50 元感谢费")
    assert result["risk_flagged"] is True
    assert "转账" in result["keywords"]
    normal = matching.submit_audit_task("捡到黑色钱包，失主请联系")
    assert normal["risk_flagged"] is False


# ---------- 流水线与接口 ----------


def test_pipeline_creates_matches_and_notifies(client):
    owner_token = register(client, "lost_owner")
    found_token = register(client, "found_owner")

    lost = publish_item(client, owner_token, "lost", "丢失黑色苹果手机")
    found = publish_item(client, found_token, "found", "捡到黑色苹果手机")
    approve_item(lost["id"])
    approve_item(found["id"])

    results = run_pipeline(lost["id"], user_id=1)
    detail = [(r["found_item_id"], r["match_score"], r["found_title"]) for r in results]
    assert len(results) >= 1
    assert results[0]["match_score"] >= 60
    assert len(results[0]["match_reason"]) >= 1
    assert results[0]["lost_item_id"] == lost["id"]
    pair = next((r for r in results if r["found_item_id"] == found["id"]), None)
    assert pair is not None, f"配对 {found['id']} 未出现在结果中: {detail}"
    assert pair["match_score"] >= 60

    # 发布者收到匹配提醒
    unread = client.get("/api/messages/unread-count", headers=auth(owner_token))
    assert unread.json()["count"] >= 1
    inbox = client.get("/api/messages", headers=auth(owner_token)).json()["items"]
    assert any(m["message_type"] == "match" for m in inbox)

    # Agent 执行日志记录了各工具
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        tools = {row.tool_name for row in db.query(AgentLog).all()}
        assert {"extract_item_attributes", "search_similar_items", "calculate_match_score", "submit_audit_task"} <= tools
    finally:
        db.close()


def test_analyze_endpoint_permissions(client):
    owner_token = register(client, "analyze_owner")
    other_token = register(client, "analyze_other")
    lost = publish_item(client, owner_token, "lost", "丢失黑色充电宝")
    approve_item(lost["id"])
    # 非发布者 → 403
    r = client.post("/api/matches/analyze", json={"item_id": lost["id"]}, headers=auth(other_token))
    assert r.status_code == 403
    # 发布者 → 200
    r2 = client.post("/api/matches/analyze", json={"item_id": lost["id"]}, headers=auth(owner_token))
    assert r2.status_code == 200
    assert r2.json()["total"] >= 0


def test_recommendations_visibility(client):
    owner_token = register(client, "rec_owner")
    lost = publish_item(client, owner_token, "lost", "丢失灰色笔记本电脑")
    # 待审核：未登录不可见
    r = client.get("/api/matches/recommendations", params={"item_id": lost["id"]})
    assert r.status_code == 404
    # 发布者可见（此时现场计算）
    r2 = client.get("/api/matches/recommendations", params={"item_id": lost["id"]}, headers=auth(owner_token))
    assert r2.status_code == 200
    # 审核后公开可见
    approve_item(lost["id"])
    r3 = client.get("/api/matches/recommendations", params={"item_id": lost["id"]})
    assert r3.status_code == 200


def test_threshold_filters_weak_matches(client):
    owner_token = register(client, "th_owner")
    found_token = register(client, "th_found")
    lost = publish_item(client, owner_token, "lost", "丢失黑色苹果手机")
    found = publish_item(client, found_token, "found", "捡到一把红色雨伞", category="雨伞水杯", color="红色", brand=None, description="九成新")
    approve_item(lost["id"])
    approve_item(found["id"])

    run_pipeline(lost["id"])
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.lost_item_id == lost["id"]).all()
        # 弱匹配（雨伞）不生成记录（共享测试库中可能存在其他高匹配物品）
        assert all(m.found_item_id != found["id"] for m in matches)
    finally:
        db.close()
