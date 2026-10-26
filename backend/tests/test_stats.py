"""公开统计接口测试。"""

import uuid


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


def test_stats_overview_is_public(client):
    r = client.get("/api/stats/overview")
    assert r.status_code == 200
    data = r.json()
    for key in (
        "items_total",
        "items_lost",
        "items_found",
        "items_claimed",
        "claims_total",
        "matches_total",
        "matches_confirmed",
        "users_total",
    ):
        assert key in data
        assert isinstance(data[key], int)


def test_stats_excludes_pending_items(client):
    before = client.get("/api/stats/overview").json()["items_total"]
    token = register(client)
    r = client.post(
        "/api/items",
        json={
            "item_type": "lost",
            "title": "统计测试待审核物品",
            "category": "其他",
            "location": "图书馆",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    )
    assert r.status_code == 201
    after = client.get("/api/stats/overview").json()["items_total"]
    assert after == before  # 待审核物品不进入公开统计
