"""套餐 A 新增接口测试：属性提取、匹配维度、图片识别标签数据。"""

import io
import uuid

from PIL import Image


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


def test_extract_attributes_requires_auth(client):
    r = client.post("/api/agent/extract", json={"text": "黑色苹果手机"})
    assert r.status_code == 401


def test_extract_attributes(client):
    token = register(client)
    r = client.post(
        "/api/agent/extract",
        json={"text": "我在图书馆丢失了一个黑色苹果手机，外面有透明壳"},
        headers=auth(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["color"] == "黑色"
    assert data["brand"] == "苹果"
    assert data["category"] == "电子数码"
    assert "图书馆" in data["location"]


def test_match_dimensions_present(client):
    from app.agents import matching
    from app.database.session import SessionLocal
    from app.models.item import Item

    token = register(client)
    lost = client.post(
        "/api/items",
        json={
            "item_type": "lost",
            "title": "维度测试黑色苹果耳机",
            "category": "电子数码",
            "color": "黑色",
            "brand": "苹果",
            "location": "图书馆",
            "latitude": 31.2304,
            "longitude": 121.4737,
            "description": "耳机盒有刻字",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    ).json()
    found = client.post(
        "/api/items",
        json={
            "item_type": "found",
            "title": "维度测试捡到黑色苹果耳机",
            "category": "电子数码",
            "color": "黑色",
            "brand": "苹果",
            "location": "图书馆",
            "latitude": 31.2304,
            "longitude": 121.4737,
            "description": "耳机盒有刻字",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    ).json()

    db = SessionLocal()
    try:
        lost_item = db.get(Item, lost["id"])
        found_item = db.get(Item, found["id"])
        lost_item.audit_status = "approved"
        found_item.audit_status = "approved"
        db.commit()
        dims = matching.calculate_match_score(lost_item, found_item)["dimensions"]
    finally:
        db.close()

    assert set(dims) == {"category", "title", "color", "brand", "time", "distance", "feature"}
    assert dims["category"] == 100
    assert dims["color"] == 100
    assert dims["brand"] == 100

    # 接口返回的匹配也带 dimensions
    results = client.get("/api/matches/recommendations", params={"item_id": lost["id"]}).json()
    assert results["total"] >= 1
    top = results["items"][0]
    assert top["dimensions"] is not None
    assert "time" in top["dimensions"]


def test_analyze_image_returns_color(client):
    token = register(client)
    buf = io.BytesIO()
    Image.new("RGB", (40, 40), (0, 0, 255)).save(buf, format="PNG")
    r = client.post(
        "/api/agent/analyze-image",
        headers=auth(token),
        files=[("file", ("blue.png", io.BytesIO(buf.getvalue()), "image/png"))],
    )
    assert r.status_code == 200
    assert r.json()["color"] == "蓝色"
