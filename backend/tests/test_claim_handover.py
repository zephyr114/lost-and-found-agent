"""新功能测试：认领描述可信度预检 + 扫码交接信息。"""

import uuid

from app.models.item import Item


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client):
    r = client.post(
        "/api/auth/register",
        json={"username": uniq("u"), "email": f"{uniq('e')}@example.com", "password": "secret123"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def publish(client, token, item_type, title, **overrides):
    payload = {
        "item_type": item_type,
        "title": title,
        "category": "电子数码",
        "color": "黑色",
        "brand": "苹果",
        "location": "图书馆",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "description": "黑色 iPhone，手机壳是透明磨砂的",
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    r = client.post("/api/items", json=payload, headers=auth(token))
    assert r.status_code == 201
    return r.json()


def approve(item_id: int) -> None:
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        item = db.get(Item, item_id)
        if item:
            item.audit_status = "approved"
            db.commit()
    finally:
        db.close()


def test_claim_check_scores_matching_description(client):
    owner = register(client)
    claimer = register(client)
    found = publish(client, owner, "found", "捡到黑色 iPhone 手机")
    approve(found["id"])

    r = client.post(
        "/api/agent/claim-check",
        json={"item_id": found["id"], "description": "我丢的是黑色 iPhone，手机壳透明磨砂，屏幕有一道划痕"},
        headers=auth(claimer),
    )
    assert r.status_code == 200
    data = r.json()
    assert 0 <= data["score"] <= 100
    assert data["verdict"] in {"high", "medium", "low"}
    assert data["score"] >= 55  # 描述与物品高度吻合


def test_claim_check_rejects_lost_item(client):
    owner = register(client)
    lost = publish(client, owner, "lost", "丢失黑色耳机")
    r = client.post(
        "/api/agent/claim-check",
        json={"item_id": lost["id"], "description": "黑色耳机"},
        headers=auth(owner),
    )
    assert r.status_code == 400


def test_handover_info_checks_code_and_participant(client):
    from app.utils.handover import generate_handover_code

    finder = register(client)
    loser = register(client)
    stranger = register(client)
    found = publish(client, finder, "found", "捡到黑色 iPhone 手机")
    lost = publish(client, loser, "lost", "丢失黑色 iPhone 手机")
    approve(found["id"])
    approve(lost["id"])

    r = client.post("/api/matches/analyze", json={"item_id": lost["id"]}, headers=auth(loser))
    assert r.status_code == 200
    matches = r.json()["items"]
    target = next(m for m in matches if m["found_item_id"] == found["id"])
    match_id = target["id"]
    code = generate_handover_code(match_id)

    ok = client.get(
        f"/api/matches/{match_id}/handover-info",
        params={"code": code},
        headers=auth(loser),
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["code_valid"] is True
    assert body["lost_item"]["id"] == lost["id"]
    assert body["found_item"]["id"] == found["id"]

    bad = client.get(
        f"/api/matches/{match_id}/handover-info",
        params={"code": "000000"},
        headers=auth(loser),
    )
    assert bad.status_code == 200
    assert bad.json()["code_valid"] is False

    denied = client.get(
        f"/api/matches/{match_id}/handover-info",
        params={"code": code},
        headers=auth(stranger),
    )
    assert denied.status_code == 403
