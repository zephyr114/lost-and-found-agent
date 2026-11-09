"""对话式发布与图像标签测试。"""

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


def test_dialog_step_fills_slots():
    from app.agents import dialog

    # 第一轮：一句话，缺地点和时间
    r1 = dialog.dialog_step("我丢了个黑色的苹果耳机", {}, "lost")
    assert "耳机" in r1["draft"]["title"]
    assert r1["draft"]["category"] == "电子数码"
    assert r1["draft"]["color"] == "黑色"
    assert r1["draft"]["brand"] == "苹果"
    assert "location" in r1["missing"]
    assert r1["next_field"] == "location"
    assert r1["options"]

    # 第二轮：补充地点
    r2 = dialog.dialog_step("在图书馆丢的", r1["draft"], "lost")
    assert r2["draft"]["location"] == "图书馆"
    assert r2["next_field"] == "event_time"

    # 第三轮：补齐时间
    r3 = dialog.dialog_step("昨天下午三点", r2["draft"], "lost")
    assert r3["draft"]["event_time"]
    assert r3["done"] is True
    assert r3["progress"] == 100


def test_dialog_location_alias():
    from app.agents import dialog

    r = dialog.dialog_step("我在一教丢的校园卡，昨天", {}, "lost")
    assert r["draft"]["location"] == "第一教学楼"
    assert r["draft"]["category"] == "证件卡类"
    assert r["done"] is True


def test_dialog_endpoint_requires_auth(client):
    r = client.post("/api/agent/dialog", json={"text": "丢了个水杯", "draft": {}, "item_type": "lost"})
    assert r.status_code == 401


def test_dialog_endpoint(client):
    token = register(client)
    r = client.post(
        "/api/agent/dialog",
        json={"text": "我在食堂丢了一个银色保温杯，昨天中午", "draft": {}, "item_type": "lost"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["draft"]["category"] == "雨伞水杯"
    assert data["draft"]["color"] == "银色"
    assert data["draft"]["location"] == "食堂"
    assert data["done"] is True
    assert data["progress"] == 100


def test_analyze_image_returns_tags(client):
    token = register(client)
    buf = io.BytesIO()
    Image.new("RGB", (400, 200), (30, 30, 30)).save(buf, format="PNG")
    r = client.post(
        "/api/agent/analyze-image",
        headers={"Authorization": f"Bearer {token}"},
        files=[("file", ("dark.png", io.BytesIO(buf.getvalue()), "image/png"))],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["color"] == "黑色"
    assert data["orientation"] == "横向"
    assert "深色系" in data["tags"]
    assert data["top_colors"]


def test_counterfactual_suggestions_improve_score():
    from datetime import datetime

    from app.agents.matching import counterfactual_suggestions
    from app.models.item import Item

    lost = Item(
        title="黑色耳机", category="电子数码", color="", brand="", location="图书馆",
        latitude=31.2304, longitude=121.4737, event_time=datetime(2026, 11, 1, 10, 0),
        description="", item_type="lost",
    )
    found = Item(
        title="捡到黑色耳机", category="电子数码", color="黑色", brand="索尼", location="食堂",
        latitude=31.2280, longitude=121.4740, event_time=datetime(2026, 11, 3, 15, 0),
        description="耳机盒有卡通贴纸", item_type="found",
    )
    suggestions = counterfactual_suggestions(lost, found)
    assert suggestions
    assert all(s["gain"] > 0 for s in suggestions)
    assert any(s["field"] == "brand" for s in suggestions)
    assert suggestions[0]["gain"] >= suggestions[-1]["gain"]


def test_precheck_flags_contact_and_short_desc(client):
    token = register(client)
    r = client.post(
        "/api/agent/precheck",
        json={"title": "转让校园卡", "description": "加微信 abc12345 私聊", "location": "食堂"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["level"] in ("medium", "high")
    assert data["reasons"]
    assert data["suggestion"]


def test_story_generated_for_resolved_item():
    from datetime import datetime

    from app.api.matches import _build_story
    from app.models.item import Item

    item = Item(
        title="银色保温杯", item_type="found", location="图书馆", status="resolved",
        audit_status="approved", event_time=datetime(2026, 11, 1, 10, 0),
        updated_at=datetime(2026, 11, 3, 10, 0),
    )
    story = _build_story(item)
    assert "银色保温杯" in story
    assert "图书馆" in story
