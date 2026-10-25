"""第四阶段验收测试：认领申请与状态流转。"""

import io
import uuid

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d4944415478da63f8cf500f00038601805a347d6b0000000049454e44ae426082"
)


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


def publish_found_item(client, token, title=None):
    """发布招领物品并置为已审核，返回 item。"""
    r = client.post(
        "/api/items",
        json={
            "item_type": "found",
            "title": title or f"捡到黑色钱包_{uniq('t')}",
            "category": "钱包箱包",
            "location": "食堂",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    )
    assert r.status_code == 201
    item = r.json()
    from app.database.session import SessionLocal
    from app.models.item import Item

    db = SessionLocal()
    try:
        it = db.get(Item, item["id"])
        it.audit_status = "approved"
        db.commit()
    finally:
        db.close()
    return item


def test_claim_requires_auth(client):
    r = client.post("/api/items/1/claims", data={"proof_description": "x"})
    assert r.status_code == 401


def test_cannot_claim_own_or_lost_item(client):
    token = register(client)
    # 失物不能认领
    lost = client.post(
        "/api/items",
        json={
            "item_type": "lost",
            "title": "丢失钱包",
            "category": "钱包箱包",
            "location": "食堂",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers=auth(token),
    ).json()
    r = client.post(
        f"/api/items/{lost['id']}/claims",
        data={"proof_description": "我的钱包"},
        headers=auth(token),
    )
    assert r.status_code == 400
    # 不能认领自己发布的招领
    found = publish_found_item(client, token)
    r = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "我的钱包"},
        headers=auth(token),
    )
    assert r.status_code == 400


def test_claim_flow_full(client):
    owner_token = register(client, "owner")
    applicant_token = register(client, "applicant")
    found = publish_found_item(client, owner_token, title="捡到苹果耳机")

    # 提交申请
    r = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "耳机盒内有我的刻字", "contact": "13800000000"},
        files=[("files", ("proof.png", io.BytesIO(TINY_PNG), "image/png"))],
        headers=auth(applicant_token),
    )
    assert r.status_code == 201
    claim = r.json()
    assert claim["status"] == "pending"
    assert len(claim["proof_images"]) == 1

    # 重复申请 → 400
    r2 = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "再次申请"},
        headers=auth(applicant_token),
    )
    assert r2.status_code == 400

    # 发布者收到通知
    unread = client.get("/api/messages/unread-count", headers=auth(owner_token))
    assert unread.json()["count"] >= 1

    # 非发布者不能审核 → 403
    r3 = client.put(f"/api/claims/{claim['id']}/approve", json={}, headers=auth(applicant_token))
    assert r3.status_code == 403

    # 要求补充证明
    r4 = client.put(
        f"/api/claims/{claim['id']}/request-proof",
        json={"review_comment": "请补充购买凭证"},
        headers=auth(owner_token),
    )
    assert r4.status_code == 200
    assert r4.json()["status"] == "need_more_proof"

    # 申请人补充证明 → 回到待处理
    r5 = client.post(
        f"/api/claims/{claim['id']}/images",
        files=[("files", ("proof2.png", io.BytesIO(TINY_PNG), "image/png"))],
        headers=auth(applicant_token),
    )
    assert r5.status_code == 200
    assert r5.json()["status"] == "pending"
    assert len(r5.json()["proof_images"]) == 2

    # 发布者同意 → 物品已认领 + 申请人收到通知
    r6 = client.put(
        f"/api/claims/{claim['id']}/approve",
        json={"review_comment": "特征吻合"},
        headers=auth(owner_token),
    )
    assert r6.status_code == 200
    assert r6.json()["status"] == "approved"
    item_detail = client.get(f"/api/items/{found['id']}", headers=auth(owner_token))
    assert item_detail.json()["status"] == "claimed"
    unread2 = client.get("/api/messages/unread-count", headers=auth(applicant_token))
    assert unread2.json()["count"] >= 1


def test_reject_claim(client):
    owner_token = register(client, "owner_r")
    applicant_token = register(client, "applicant_r")
    found = publish_found_item(client, owner_token, title="捡到雨伞")
    claim = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "伞柄有贴纸"},
        headers=auth(applicant_token),
    ).json()

    r = client.put(
        f"/api/claims/{claim['id']}/reject",
        json={"review_comment": "特征不符"},
        headers=auth(owner_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    # 物品仍可认领
    detail = client.get(f"/api/items/{found['id']}", headers=auth(owner_token))
    assert detail.json()["status"] == "active"


def test_approve_auto_rejects_others(client):
    owner_token = register(client, "owner_m")
    a_token = register(client, "applicant_a")
    b_token = register(client, "applicant_b")
    found = publish_found_item(client, owner_token, title="捡到黑色书包")

    claim_a = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "A 的证明"},
        headers=auth(a_token),
    ).json()
    claim_b = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "B 的证明"},
        headers=auth(b_token),
    ).json()

    r = client.put(f"/api/claims/{claim_a['id']}/approve", json={}, headers=auth(owner_token))
    assert r.status_code == 200

    my_claims = client.get("/api/claims/my", headers=auth(b_token))
    b_claim = next(c for c in my_claims.json()["items"] if c["id"] == claim_b["id"])
    assert b_claim["status"] == "rejected"


def test_cancel_claim(client):
    owner_token = register(client, "owner_c")
    applicant_token = register(client, "applicant_c")
    found = publish_found_item(client, owner_token, title="捡到水杯")
    claim = client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "杯盖有裂痕"},
        headers=auth(applicant_token),
    ).json()

    r = client.delete(f"/api/claims/{claim['id']}", headers=auth(applicant_token))
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_claim_lists(client):
    owner_token = register(client, "owner_l")
    applicant_token = register(client, "applicant_l")
    found = publish_found_item(client, owner_token, title="捡到校园卡")
    client.post(
        f"/api/items/{found['id']}/claims",
        data={"proof_description": "卡号后四位 1234"},
        headers=auth(applicant_token),
    )
    my = client.get("/api/claims/my", headers=auth(applicant_token))
    assert my.status_code == 200
    assert my.json()["total"] >= 1
    assert my.json()["items"][0]["item_title"] == "捡到校园卡"

    received = client.get("/api/claims/received", headers=auth(owner_token))
    assert received.status_code == 200
    assert received.json()["total"] >= 1
    assert received.json()["items"][0]["applicant_name"]
