"""套餐 B 测试：交接码、已找回、故事墙、消息回复。"""

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
        "title": "交接测试物品",
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


def make_pair(client):
    from app.agents import matching
    from app.database.session import SessionLocal

    lost_owner = register(client, "ho_lost")
    found_owner = register(client, "ho_found")
    lost = publish(client, lost_owner, "lost", title="交接测试丢失耳机")
    found = publish(client, found_owner, "found", title="交接测试捡到耳机")
    approve(lost["id"])
    approve(found["id"])
    db = SessionLocal()
    try:
        results = matching.run_matching_pipeline(db, lost["id"], notify=False)
    finally:
        db.close()
    pair = next((r for r in results if r["found_item_id"] == found["id"]), None)
    assert pair is not None
    return lost_owner, found_owner, lost, found, pair["id"]


def test_handover_full_flow(client):
    lost_owner, found_owner, lost, found, match_id = make_pair(client)

    # 确认匹配前不能看交接码
    r = client.get(f"/api/matches/{match_id}/code", headers=auth(lost_owner))
    assert r.status_code == 400

    # 失主确认匹配 → 返回交接码
    r = client.post(f"/api/matches/{match_id}/confirm", headers=auth(lost_owner))
    assert r.status_code == 200
    code = r.json()["handover_code"]
    assert code and len(code) == 6

    # 双方都能查到同一个交接码
    r2 = client.get(f"/api/matches/{match_id}/code", headers=auth(found_owner))
    assert r2.status_code == 200
    assert r2.json()["handover_code"] == code

    # 未参与确认交接 → 403
    outsider = register(client, "ho_out")
    r3 = client.post(f"/api/matches/{match_id}/handover", json={"code": code}, headers=auth(outsider))
    assert r3.status_code == 403

    # 错误交接码 → 400
    r4 = client.post(f"/api/matches/{match_id}/handover", json={"code": "000000"}, headers=auth(found_owner))
    assert r4.status_code == 400

    # 正确交接码 → 200，状态 handed_over
    r5 = client.post(f"/api/matches/{match_id}/handover", json={"code": code}, headers=auth(found_owner))
    assert r5.status_code == 200
    assert r5.json()["status"] == "handed_over"

    # 两个物品都变成已找回
    lost_detail = client.get(f"/api/items/{lost['id']}", headers=auth(lost_owner))
    found_detail = client.get(f"/api/items/{found['id']}", headers=auth(found_owner))
    assert lost_detail.json()["status"] == "resolved"
    assert found_detail.json()["status"] == "resolved"

    # 双方收到交接完成通知
    inbox = client.get("/api/messages", headers=auth(found_owner)).json()["items"]
    assert any("交接" in m["content"] for m in inbox)

    # 故事墙包含该物品
    stories = client.get("/api/matches/stories")
    assert stories.status_code == 200
    assert any(s["id"] == lost["id"] for s in stories.json()["items"])

    # 重复交接幂等
    r6 = client.post(f"/api/matches/{match_id}/handover", json={"code": code}, headers=auth(found_owner))
    assert r6.status_code == 200


def test_stories_public_and_limited(client):
    r = client.get("/api/matches/stories", params={"limit": 3})
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 3


def test_message_reply_via_send(client):
    a = register(client, "reply_a")
    b = register(client, "reply_b")
    # 模拟 B 回复 A 的消息
    a_id = client.get("/api/users/me", headers=auth(a)).json()["id"]
    r = client.post("/api/messages/send", json={"receiver_id": a_id, "content": "收到，谢谢！"}, headers=auth(b))
    assert r.status_code == 201
    inbox = client.get("/api/messages", headers=auth(a)).json()["items"]
    assert any(m["content"] == "收到，谢谢！" for m in inbox)
