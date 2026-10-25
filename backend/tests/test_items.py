"""第三阶段验收测试：发布、搜索、详情、编辑、删除、图片上传。"""

import base64
import io
import uuid

# 1x1 透明 PNG
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client, username=None):
    payload = {
        "username": username or uniq("u"),
        "email": f"{uniq('e')}@example.com",
        "password": "secret123",
    }
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 201
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def item_payload(**overrides):
    payload = {
        "item_type": "lost",
        "title": "黑色双肩包",
        "category": "钱包箱包",
        "description": "包内有钥匙和充电宝",
        "color": "黑色",
        "brand": "耐克",
        "location": "图书馆三楼",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    return payload


def approve_item(item_id: int):
    """测试辅助：直接把物品置为已审核（管理审核接口在第六阶段）。"""
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


# ---------- 发布 ----------


def test_create_item_requires_auth(client):
    r = client.post("/api/items", json=item_payload())
    assert r.status_code == 401


def test_create_and_get_own_item(client):
    token = register(client)
    r = client.post("/api/items", json=item_payload(), headers=auth(token))
    assert r.status_code == 201
    data = r.json()
    assert data["item_type"] == "lost"
    assert data["audit_status"] == "pending"  # 发布后进入审核状态
    assert data["username"]  # 带发布者用户名
    # 发布者本人可以查看待审核物品
    detail = client.get(f"/api/items/{data['id']}", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["title"] == "黑色双肩包"


def test_pending_item_hidden_from_public(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    # 未登录看不到
    assert client.get(f"/api/items/{item_id}").status_code == 404
    assert client.get("/api/items").json()["total"] == 0
    # 其他用户也看不到
    other = register(client)
    assert client.get(f"/api/items/{item_id}", headers=auth(other)).status_code == 404
    # 管理员可见
    admin_login = client.post("/api/auth/login", json={"account": "admin@example.com", "password": "admin123456"})
    admin_token = admin_login.json()["access_token"]
    assert client.get(f"/api/items/{item_id}", headers=auth(admin_token)).status_code == 200


# ---------- 搜索与筛选 ----------


def test_list_filters(client):
    token = register(client)
    # 已审核的失物
    lost = client.post("/api/items", json=item_payload(), headers=auth(token)).json()
    approve_item(lost["id"])
    # 已审核的招领
    found = client.post(
        "/api/items",
        json=item_payload(item_type="found", title="捡到黑色钱包", category="钱包箱包", location="食堂"),
        headers=auth(token),
    ).json()
    approve_item(found["id"])

    # 类型筛选
    r = client.get("/api/items", params={"item_type": "lost"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert all(i["item_type"] == "lost" for i in r.json()["items"])

    # 关键词搜索
    r = client.get("/api/items", params={"q": "钱包"})
    assert any("钱包" in i["title"] for i in r.json()["items"])

    # 分类筛选
    r = client.get("/api/items", params={"category": "钱包箱包"})
    assert all(i["category"] == "钱包箱包" for i in r.json()["items"])

    # 地点筛选
    r = client.get("/api/items", params={"location": "食堂"})
    assert any("食堂" in i["location"] for i in r.json()["items"])


def test_distance_sort(client):
    token = register(client)
    # 近：上海人民广场
    near = client.post(
        "/api/items",
        json=item_payload(title="近的物品", latitude=31.2304, longitude=121.4737),
        headers=auth(token),
    ).json()
    approve_item(near["id"])
    # 远：北京天安门
    far = client.post(
        "/api/items",
        json=item_payload(title="远的物品", latitude=39.9087, longitude=116.3975),
        headers=auth(token),
    ).json()
    approve_item(far["id"])

    r = client.get("/api/items", params={"sort": "distance", "lat": 31.23, "lng": 121.47})
    ids = [i["id"] for i in r.json()["items"]]
    assert ids.index(near["id"]) < ids.index(far["id"])


# ---------- 编辑与删除 ----------


def test_update_item_resets_audit(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    approve_item(item_id)
    r = client.put(f"/api/items/{item_id}", json={"title": "灰色双肩包"}, headers=auth(token))
    assert r.status_code == 200
    assert r.json()["title"] == "灰色双肩包"
    assert r.json()["audit_status"] == "pending"  # 修改后重新审核


def test_update_denied_for_other_user(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    other = register(client)
    assert client.put(f"/api/items/{item_id}", json={"title": "x"}, headers=auth(other)).status_code == 403


def test_delete_item(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    # 他人删除 → 403
    other = register(client)
    assert client.delete(f"/api/items/{item_id}", headers=auth(other)).status_code == 403
    # 本人删除 → 200
    assert client.delete(f"/api/items/{item_id}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/items/{item_id}", headers=auth(token)).status_code == 404


# ---------- 图片上传 ----------


def test_image_upload_and_serving(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    r = client.post(
        f"/api/items/{item_id}/images",
        headers=auth(token),
        files=[("files", ("photo.png", io.BytesIO(TINY_PNG), "image/png"))],
    )
    assert r.status_code == 200
    images = r.json()["images"]
    assert len(images) == 1
    assert images[0].startswith("/uploads/")
    # 图片可通过 /uploads 访问
    resp = client.get(images[0])
    assert resp.status_code == 200
    assert resp.content == TINY_PNG


def test_image_upload_rejects_non_image(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    r = client.post(
        f"/api/items/{item_id}/images",
        headers=auth(token),
        files=[("files", ("evil.exe", io.BytesIO(b"MZ fake exe"), "application/octet-stream"))],
    )
    assert r.status_code == 400


def test_image_upload_denied_for_other_user(client):
    token = register(client)
    item_id = client.post("/api/items", json=item_payload(), headers=auth(token)).json()["id"]
    other = register(client)
    r = client.post(
        f"/api/items/{item_id}/images",
        headers=auth(other),
        files=[("files", ("photo.png", io.BytesIO(TINY_PNG), "image/png"))],
    )
    assert r.status_code == 403


def test_categories_endpoint(client):
    r = client.get("/api/items/categories")
    assert r.status_code == 200
    assert "钱包箱包" in r.json()["categories"]
