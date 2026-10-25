"""第六阶段验收测试：管理后台。"""

import uuid

from app.core.config import settings


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
    return r.json()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_token(client):
    r = client.post("/api/auth/login", json={"account": settings.admin_email, "password": settings.admin_password})
    assert r.status_code == 200
    return r.json()["access_token"]


def publish_item(client, token, item_type="lost", **overrides):
    payload = {
        "item_type": item_type,
        "title": f"物品_{uniq('t')}",
        "category": "其他",
        "location": "某地",
        "event_time": "2026-10-20T10:00:00Z",
    }
    payload.update(overrides)
    r = client.post("/api/items", json=payload, headers=auth(token))
    assert r.status_code == 201
    return r.json()


def test_admin_endpoints_require_admin(client):
    user = register(client)
    for path in ("/api/admin/statistics", "/api/admin/items/pending", "/api/admin/agent-logs"):
        r = client.get(path, headers=auth(user["access_token"]))
        assert r.status_code == 403


def test_statistics_shape(client):
    r = client.get("/api/admin/statistics", headers=auth(admin_token(client)))
    assert r.status_code == 200
    data = r.json()
    for key in ("users_total", "items_total", "items_pending_audit", "claims_total", "matches_total", "reports_pending"):
        assert key in data


def test_audit_item_approve_and_notify(client):
    user = register(client)
    item = publish_item(client, user["access_token"], title="待审核物品A")
    adm = admin_token(client)

    # 待审核列表可见
    pending = client.get("/api/admin/items/pending", headers=auth(adm))
    assert any(i["id"] == item["id"] for i in pending.json()["items"])

    # 通过审核
    r = client.put(f"/api/admin/items/{item['id']}/audit", json={"decision": "approve", "comment": "ok"}, headers=auth(adm))
    assert r.status_code == 200
    assert r.json()["audit_status"] == "approved"

    # 公开可见
    detail = client.get(f"/api/items/{item['id']}")
    assert detail.status_code == 200

    # 发布者收到审核通知
    inbox = client.get("/api/messages", headers=auth(user["access_token"])).json()["items"]
    assert any(m["message_type"] == "audit" for m in inbox)


def test_audit_item_reject(client):
    user = register(client)
    item = publish_item(client, user["access_token"], title="待审核物品B")
    adm = admin_token(client)
    r = client.put(f"/api/admin/items/{item['id']}/audit", json={"decision": "reject", "comment": "信息不全"}, headers=auth(adm))
    assert r.status_code == 200
    detail = client.get(f"/api/items/{item['id']}", headers=auth(user["access_token"]))
    assert detail.json()["audit_status"] == "rejected"
    # 公开不可见
    assert client.get(f"/api/items/{item['id']}").status_code == 404


def test_user_disable_and_login_blocked(client):
    user = register(client)
    adm = admin_token(client)
    r = client.put(f"/api/admin/users/{user['user']['id']}/status", json={"status": "disabled"}, headers=auth(adm))
    assert r.status_code == 200
    # 禁用后无法登录
    login = client.post("/api/auth/login", json={"account": user["user"]["email"], "password": "secret123"})
    assert login.status_code == 403
    # 恢复后可登录
    client.put(f"/api/admin/users/{user['user']['id']}/status", json={"status": "active"}, headers=auth(adm))
    assert client.post("/api/auth/login", json={"account": user["user"]["email"], "password": "secret123"}).status_code == 200


def test_cannot_disable_admin(client):
    adm = admin_token(client)
    me = client.get("/api/users/me", headers=auth(adm)).json()
    r = client.put(f"/api/admin/users/{me['id']}/status", json={"status": "disabled"}, headers=auth(adm))
    assert r.status_code == 400


def test_report_flow(client):
    owner = register(client, "report_owner")
    reporter = register(client, "reporter")
    item = publish_item(client, owner["access_token"], title="可疑物品")
    # 提交举报
    r = client.post(
        "/api/reports",
        json={"target_type": "item", "target_id": item["id"], "reason": "虚假信息", "description": "内容不实"},
        headers=auth(reporter["access_token"]),
    )
    assert r.status_code == 201
    report_id = r.json()["id"]
    # 管理员处理
    adm = admin_token(client)
    r2 = client.put(
        f"/api/admin/reports/{report_id}/handle",
        json={"action": "handled", "comment": "已删除该信息"},
        headers=auth(adm),
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "handled"
    # 举报人收到处理通知
    inbox = client.get("/api/messages", headers=auth(reporter["access_token"])).json()["items"]
    assert any(m["message_type"] == "report" for m in inbox)
    # 我的举报列表
    my = client.get("/api/reports/my", headers=auth(reporter["access_token"]))
    assert my.json()["total"] >= 1


def test_announcement_crud(client):
    adm = admin_token(client)
    r = client.post("/api/admin/announcements", json={"title": "系统维护通知", "content": "本周六 0-6 点系统维护"}, headers=auth(adm))
    assert r.status_code == 201
    ann_id = r.json()["id"]
    # 公开接口可见
    public = client.get("/api/announcements")
    assert any(a["id"] == ann_id for a in public.json())
    # 编辑
    r2 = client.put(f"/api/admin/announcements/{ann_id}", json={"title": "系统维护通知（更新）"}, headers=auth(adm))
    assert r2.json()["title"] == "系统维护通知（更新）"
    # 归档后公开接口不可见
    client.put(f"/api/admin/announcements/{ann_id}", json={"status": "archived"}, headers=auth(adm))
    public2 = client.get("/api/announcements")
    assert not any(a["id"] == ann_id for a in public2.json())
    # 删除
    assert client.delete(f"/api/admin/announcements/{ann_id}", headers=auth(adm)).status_code == 200


def test_operation_and_agent_logs(client):
    user = register(client)
    item = publish_item(client, user["access_token"], title="日志测试物品")
    adm = admin_token(client)
    client.put(f"/api/admin/items/{item['id']}/audit", json={"decision": "approve"}, headers=auth(adm))
    # 操作日志记录了审核
    ops = client.get("/api/admin/operation-logs", headers=auth(adm)).json()["items"]
    assert any(o["action"] == "item_approve" and o["target_id"] == item["id"] for o in ops)
    # Agent 日志存在（审核通过触发匹配）
    logs = client.get("/api/admin/agent-logs", headers=auth(adm)).json()["items"]
    assert len(logs) >= 1
    assert any(l["tool_name"] == "extract_item_attributes" for l in logs)


def test_admin_delete_item(client):
    user = register(client)
    item = publish_item(client, user["access_token"], title="违规物品")
    adm = admin_token(client)
    r = client.delete(f"/api/admin/items/{item['id']}", headers=auth(adm))
    assert r.status_code == 200
    assert client.get(f"/api/items/{item['id']}", headers=auth(user["access_token"])).status_code == 404
