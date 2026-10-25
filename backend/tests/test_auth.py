"""第二阶段验收测试：注册、登录、JWT 鉴权、角色权限。"""

import uuid

from app.core.config import settings


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register_payload(**overrides):
    payload = {
        "username": uniq("user"),
        "email": f"{uniq('u')}@example.com",
        "phone": f"1{uuid.uuid4().hex[:10]}",
        "password": "secret123",
    }
    payload.update(overrides)
    return payload


# ---------- 注册 ----------


def test_register_success(client):
    r = client.post("/api/auth/register", json=register_payload())
    assert r.status_code == 201
    data = r.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "user"
    assert data["user"]["status"] == "active"
    assert data["user"]["credit_score"] == 100
    assert "password_hash" not in r.text  # 绝不返回密码哈希


def test_register_duplicate_username(client):
    payload = register_payload()
    assert client.post("/api/auth/register", json=payload).status_code == 201
    payload["email"] = f"{uniq('d')}@example.com"  # 换邮箱但用户名相同
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_duplicate_email(client):
    payload = register_payload()
    assert client.post("/api/auth/register", json=payload).status_code == 201
    payload["username"] = uniq("other")  # 换用户名但邮箱相同
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_invalid_email_and_short_password(client):
    payload = register_payload(email="not-an-email", password="123")
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 422


# ---------- 登录与鉴权 ----------


def test_login_success_by_username_and_email(client):
    payload = register_payload()
    assert client.post("/api/auth/register", json=payload).status_code == 201
    # 用户名登录
    r1 = client.post("/api/auth/login", json={"account": payload["username"], "password": "secret123"})
    assert r1.status_code == 200
    # 邮箱登录
    r2 = client.post("/api/auth/login", json={"account": payload["email"], "password": "secret123"})
    assert r2.status_code == 200
    # 手机号登录
    r3 = client.post("/api/auth/login", json={"account": payload["phone"], "password": "secret123"})
    assert r3.status_code == 200


def test_login_wrong_password(client):
    payload = register_payload()
    client.post("/api/auth/register", json=payload)
    r = client.post("/api/auth/login", json={"account": payload["username"], "password": "wrong123"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    # 未登录访问受保护接口 → 401
    assert client.get("/api/users/me").status_code == 401
    # 伪造 token → 401
    assert client.get("/api/users/me", headers=auth_header("not-a-valid-token")).status_code == 401


def test_me_with_token(client):
    payload = register_payload()
    token = client.post("/api/auth/register", json=payload).json()["access_token"]
    r = client.get("/api/users/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["username"] == payload["username"]


# ---------- 角色权限 ----------


def test_admin_api_denied_for_normal_user(client):
    token = client.post("/api/auth/register", json=register_payload()).json()["access_token"]
    r = client.get("/api/admin/users", headers=auth_header(token))
    assert r.status_code == 403


def test_admin_api_allowed_for_admin(client):
    login = client.post(
        "/api/auth/login",
        json={"account": settings.admin_email, "password": settings.admin_password},
    )
    assert login.status_code == 200
    admin_token = login.json()["access_token"]
    r = client.get("/api/admin/users", headers=auth_header(admin_token))
    assert r.status_code == 200
    users = r.json()["items"]
    assert any(u["role"] == "admin" for u in users)


# ---------- 个人资料与密码 ----------


def test_update_profile(client):
    token = client.post("/api/auth/register", json=register_payload()).json()["access_token"]
    r = client.put(
        "/api/users/me",
        json={"avatar": "https://example.com/a.png", "phone": "13800000000"},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["avatar"] == "https://example.com/a.png"
    assert data["phone"] == "13800000000"


def test_change_password_flow(client):
    payload = register_payload()
    token = client.post("/api/auth/register", json=payload).json()["access_token"]
    # 原密码错误 → 400
    bad = client.put(
        "/api/users/me/password",
        json={"old_password": "wrong123", "new_password": "newpass123"},
        headers=auth_header(token),
    )
    assert bad.status_code == 400
    # 正确修改
    ok = client.put(
        "/api/users/me/password",
        json={"old_password": "secret123", "new_password": "newpass123"},
        headers=auth_header(token),
    )
    assert ok.status_code == 200
    # 新密码可登录，旧密码失效
    assert client.post("/api/auth/login", json={"account": payload["username"], "password": "newpass123"}).status_code == 200
    assert client.post("/api/auth/login", json={"account": payload["username"], "password": "secret123"}).status_code == 401
