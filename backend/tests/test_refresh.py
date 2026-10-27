"""套餐 C 测试：刷新令牌。"""

import uuid

import jwt

from app.core.config import settings


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register(client):
    r = client.post(
        "/api/auth/register",
        json={"username": uniq("u"), "email": f"{uniq('e')}@example.com", "password": "secret123"},
    )
    assert r.status_code == 201
    return r.json()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_refresh_token(client):
    data = register(client)
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_refresh_flow(client):
    data = register(client)
    refresh_token = data["refresh_token"]
    # 用刷新令牌换新访问令牌
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    assert new_access
    # 新令牌可用
    me = client.get("/api/users/me", headers=auth(new_access))
    assert me.status_code == 200
    # 刷新令牌也旋转了
    assert r.json()["refresh_token"]


def test_refresh_with_access_token_rejected(client):
    data = register(client)
    r = client.post("/api/auth/refresh", json={"refresh_token": data["access_token"]})
    assert r.status_code == 401


def test_refresh_with_invalid_token(client):
    r = client.post("/api/auth/refresh", json={"refresh_token": "not-a-valid-token"})
    assert r.status_code == 401


def test_refresh_token_expiry_claim(client):
    """刷新令牌应带 type=refresh 与较长过期时间。"""
    data = register(client)
    payload = jwt.decode(data["refresh_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["type"] == "refresh"
    assert payload["exp"] > payload["iat"]
