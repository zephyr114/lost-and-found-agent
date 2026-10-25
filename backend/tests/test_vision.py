"""图片识别功能测试：主色检测、接口与流水线集成。"""

import io
import uuid

from PIL import Image

from app.utils.vision import analyze_image_local, resolve_upload_path


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


def make_png(color: tuple[int, int, int], size=(40, 40)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


# ---------- 本地主色检测 ----------


def test_analyze_image_local_red(tmp_path):
    p = tmp_path / "red.png"
    Image.new("RGB", (40, 40), (255, 0, 0)).save(p)
    result = analyze_image_local(p)
    assert result["color"] == "红色"
    assert result["brightness"] is not None


def test_analyze_image_local_black(tmp_path):
    p = tmp_path / "black.png"
    Image.new("RGB", (40, 40), (0, 0, 0)).save(p)
    assert analyze_image_local(p)["color"] == "黑色"


def test_resolve_upload_path():
    path = resolve_upload_path("/uploads/2026/10/abc.png")
    assert path is not None and str(path).endswith("uploads/2026/10/abc.png".replace("/", "\\"))
    assert resolve_upload_path("https://example.com/x.png") is None
    assert resolve_upload_path(None) is None


# ---------- 接口 ----------


def test_analyze_image_endpoint(client):
    token = register(client)
    r = client.post(
        "/api/agent/analyze-image",
        headers=auth(token),
        files=[("file", ("red.png", io.BytesIO(make_png((255, 0, 0))), "image/png"))],
    )
    assert r.status_code == 200
    data = r.json()
    assert data["color"] == "红色"
    assert data["image_url"].startswith("/uploads/")


def test_analyze_image_requires_auth(client):
    r = client.post("/api/agent/analyze-image", files=[("file", ("x.png", io.BytesIO(make_png((255, 0, 0))), "image/png"))])
    assert r.status_code == 401


# ---------- 流水线集成：图片补充颜色 ----------


def test_pipeline_enriches_color_from_image(client):
    from app.agents import matching
    from app.database.session import SessionLocal
    from app.models.item import Item

    token = register(client)
    # 发布不带颜色的失物并上传一张纯蓝图片
    r = client.post(
        "/api/items",
        json={
            "item_type": "lost",
            "title": "丢失蓝色物品",
            "category": "其他",
            "location": "某地",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    )
    assert r.status_code == 201
    item = r.json()
    client.post(
        f"/api/items/{item['id']}/images",
        headers=auth(token),
        files=[("files", ("blue.png", io.BytesIO(make_png((0, 0, 255))), "image/png"))],
    )

    # 直接跑流水线（本地图片识别路径）
    db = SessionLocal()
    try:
        matching.run_matching_pipeline(db, item["id"], user_id=item["user_id"], notify=False)
        refreshed = db.get(Item, item["id"])
        assert refreshed.color == "蓝色"  # 图片识别补全了颜色
    finally:
        db.close()
