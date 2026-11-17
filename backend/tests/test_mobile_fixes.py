"""实测问题回归测试：图片 EXIF 方向、认领联系方式兜底。"""

import io
import uuid

from PIL import Image


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client):
    username = uniq("u")
    email = f"{uniq('e')}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "secret123"},
    )
    assert r.status_code == 201
    return r.json()["access_token"], email


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def publish(client, token, item_type, title, **overrides):
    payload = {
        "item_type": item_type,
        "title": title,
        "category": "电子数码",
        "color": "黑色",
        "brand": "苹果",
        "location": "正心楼",
        "latitude": 30.08,
        "longitude": 120.58,
        "description": "黑色手机，透明磨砂壳",
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    r = client.post("/api/items", json=payload, headers=auth(token))
    assert r.status_code == 201
    return r.json()


def approve(item_id: int) -> None:
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


def test_upload_applies_exif_orientation(client):
    token, _ = register(client)
    item = publish(client, token, "found", "捡到黑色手机")
    approve(item["id"])

    # 40x20 的图，EXIF orientation=6（需顺时针旋转 90°）
    img = Image.new("RGB", (40, 20), (200, 30, 30))
    exif = Image.Exif()
    exif[274] = 6
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)

    r = client.post(
        f"/api/items/{item['id']}/images",
        headers=auth(token),
        files=[("files", ("rotated.jpg", buf.getvalue(), "image/jpeg"))],
    )
    assert r.status_code == 200
    url = r.json()["images"][0]

    data = client.get(url).content
    out = Image.open(io.BytesIO(data))
    assert out.size == (20, 40), f"EXIF 未生效，尺寸为 {out.size}"


def test_claim_contact_falls_back_to_applicant_email(client):
    owner, _ = register(client)
    claimer, claimer_email = register(client)
    item = publish(client, owner, "found", "捡到黑色手机")
    approve(item["id"])

    r = client.post(
        f"/api/items/{item['id']}/claims",
        headers=auth(claimer),
        data={"proof_description": "我的手机，壳是透明磨砂的", "contact": ""},
    )
    assert r.status_code == 201
    claim_id = r.json()["id"]

    # 发布者视角应能看到申请人邮箱（contact 兜底）
    r = client.get("/api/claims/received", headers=auth(owner))
    assert r.status_code == 200
    row = next(c for c in r.json()["items"] if c["id"] == claim_id)
    assert row["contact"] == claimer_email

    # 批准应成功
    r = client.put(f"/api/claims/{claim_id}/approve", json={"review_comment": None}, headers=auth(owner))
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
