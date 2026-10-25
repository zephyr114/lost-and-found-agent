"""第四阶段验收测试：站内消息。"""

import uuid


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


def test_messages_require_auth(client):
    assert client.get("/api/messages").status_code == 401


def test_send_message_and_inbox(client):
    a_token = register(client, "sender")
    b = client.post(
        "/api/auth/register",
        json={"username": uniq("receiver"), "email": f"{uniq('r')}@example.com", "password": "secret123"},
    ).json()
    b_token = b["access_token"]
    b_id = b["user"]["id"]

    # 发送私信
    r = client.post("/api/messages/send", json={"receiver_id": b_id, "content": "你好，请问钱包在哪里捡到的？"}, headers=auth(a_token))
    assert r.status_code == 201
    assert r.json()["sender_name"] == "sender"

    # B 收件箱可见，未读 1
    inbox = client.get("/api/messages", params={"box": "inbox"}, headers=auth(b_token))
    assert inbox.json()["total"] >= 1
    msg = inbox.json()["items"][0]
    assert msg["content"].startswith("你好")
    assert msg["is_read"] is False
    assert client.get("/api/messages/unread-count", headers=auth(b_token)).json()["count"] >= 1

    # 标记已读
    r2 = client.put(f"/api/messages/{msg['id']}/read", headers=auth(b_token))
    assert r2.status_code == 200
    assert r2.json()["is_read"] is True
    assert client.get("/api/messages/unread-count", headers=auth(b_token)).json()["count"] == 0

    # A 的发件箱可见
    sent = client.get("/api/messages", params={"box": "sent"}, headers=auth(a_token))
    assert sent.json()["total"] >= 1


def test_mark_read_requires_receiver(client):
    a_token = register(client, "sender2")
    b = client.post(
        "/api/auth/register",
        json={"username": uniq("receiver2"), "email": f"{uniq('r2')}@example.com", "password": "secret123"},
    ).json()
    b_id = b["user"]["id"]
    b_token = b["access_token"]

    msg = client.post("/api/messages/send", json={"receiver_id": b_id, "content": "test"}, headers=auth(a_token)).json()
    # 第三方不能标记已读
    c_token = register(client, "third")
    r = client.put(f"/api/messages/{msg['id']}/read", headers=auth(c_token))
    assert r.status_code == 403
    # 收件人可以
    assert client.put(f"/api/messages/{msg['id']}/read", headers=auth(b_token)).status_code == 200


def test_send_message_validation(client):
    a_token = register(client, "sender3")
    # 发给自己 → 400
    me = client.get("/api/users/me", headers=auth(a_token)).json()
    r = client.post("/api/messages/send", json={"receiver_id": me["id"], "content": "hi"}, headers=auth(a_token))
    assert r.status_code == 400
    # 收件人不存在 → 404
    r2 = client.post("/api/messages/send", json={"receiver_id": 999999, "content": "hi"}, headers=auth(a_token))
    assert r2.status_code == 404
    # 空内容 → 422
    r3 = client.post("/api/messages/send", json={"receiver_id": 999999, "content": ""}, headers=auth(a_token))
    assert r3.status_code == 422


def test_read_all(client):
    b = client.post(
        "/api/auth/register",
        json={"username": uniq("reader"), "email": f"{uniq('rd')}@example.com", "password": "secret123"},
    ).json()
    b_token = b["access_token"]
    b_id = b["user"]["id"]
    a_token = register(client, "sender4")
    for i in range(2):
        client.post("/api/messages/send", json={"receiver_id": b_id, "content": f"msg{i}"}, headers=auth(a_token))
    assert client.get("/api/messages/unread-count", headers=auth(b_token)).json()["count"] >= 2
    r = client.put("/api/messages/read-all", headers=auth(b_token))
    assert r.status_code == 200
    assert client.get("/api/messages/unread-count", headers=auth(b_token)).json()["count"] == 0
