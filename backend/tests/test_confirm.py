"""匹配确认（这是我的物品）功能测试。"""

import uuid


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client, name=None):
    r = client.post(
        "/api/auth/register",
        json={
            "username": name or uniq("u"),
            "email": f"{uniq('e')}@example.com",
            "password": "secret123",
        },
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def publish(client, token, item_type, **overrides):
    payload = {
        "item_type": item_type,
        "title": "确认测试物品",
        "category": "电子数码",
        "color": "黑色",
        "brand": "苹果",
        "location": "图书馆",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    r = client.post("/api/items", json=payload, headers=auth(token))
    assert r.status_code == 201
    return r.json()


def approve(item_id: int):
    from app.database.session import SessionLocal
    from app.models.item import Item

    db = SessionLocal()
    try:
        item = db.get(Item, item_id)
        if item:
            item.audit_status = "approved"
            db.commit()
    finally:
        db.close()


def test_confirm_match_flow(client):
    from app.agents import matching
    from app.database.session import SessionLocal

    lost_owner = register(client, "lost_owner_c")
    found_owner = register(client, "found_owner_c")
    lost = publish(client, lost_owner, "lost", title="丢失黑色苹果手机C")
    found = publish(client, found_owner, "found", title="捡到黑色苹果手机C")
    approve(lost["id"])
    approve(found["id"])

    db = SessionLocal()
    try:
        results = matching.run_matching_pipeline(db, lost["id"], notify=False)
    finally:
        db.close()
    pair = next((r for r in results if r["found_item_id"] == found["id"]), None)
    assert pair is not None, "应生成失物与招领的匹配记录"
    match_id = pair["id"]

    # 非失主确认 → 403
    r = client.post(f"/api/matches/{match_id}/confirm", headers=auth(found_owner))
    assert r.status_code == 403
    # 未登录 → 401
    assert client.post(f"/api/matches/{match_id}/confirm").status_code == 401
    # 失主确认 → 200 且状态为 confirmed
    r2 = client.post(f"/api/matches/{match_id}/confirm", headers=auth(lost_owner))
    assert r2.status_code == 200
    assert r2.json()["status"] == "confirmed"
    # 招领发布者收到通知
    inbox = client.get("/api/messages", headers=auth(found_owner)).json()["items"]
    assert any(m["message_type"] == "match" for m in inbox)
    # 重复确认幂等
    r3 = client.post(f"/api/matches/{match_id}/confirm", headers=auth(lost_owner))
    assert r3.status_code == 200
