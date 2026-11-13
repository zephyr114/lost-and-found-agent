"""套餐 C 测试：限流中间件（数据库计数版）。"""

import time

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.ratelimit import RateLimitMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, auth_limit=3, global_limit=10, window_seconds=60)

    @app.get("/api/auth/ping")
    def auth_ping():
        return {"ok": True}

    @app.get("/api/other")
    def other():
        return {"ok": True}

    return app


def _client(ip: str) -> TestClient:
    """每个用例用独立 IP，避免共享同一限流窗口。"""
    return TestClient(_make_app(), client=(ip, 10000))


def test_auth_rate_limit_blocks_after_threshold():
    client = _client("10.9.0.1")
    codes = [client.get("/api/auth/ping").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429
    assert codes[4] == 429


def test_global_limit_separate_from_auth():
    client = _client("10.9.0.2")
    # 认证桶被限流后，普通接口不受影响
    for _ in range(4):
        client.get("/api/auth/ping")
    assert client.get("/api/other").status_code == 200


def test_429_has_chinese_detail():
    client = _client("10.9.0.3")
    for _ in range(3):
        client.get("/api/auth/ping")
    r = client.get("/api/auth/ping")
    assert r.status_code == 429
    assert "频繁" in r.json()["detail"]


def test_rate_limit_counter_increments(client):
    """数据库计数：同一窗口内每次请求 +1。"""
    from app.core.ratelimit import _hit

    window = int(time.time()) // 60
    key = f"test:rl:{time.time_ns()}"
    values = [_hit(key, window, 5) for _ in range(6)]

    assert values[0] == 1
    assert values[-1] == 6
    assert values[-1] > 5
