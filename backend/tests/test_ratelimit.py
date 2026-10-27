"""套餐 C 测试：限流中间件。"""

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


def test_auth_rate_limit_blocks_after_threshold():
    client = TestClient(_make_app())
    codes = [client.get("/api/auth/ping").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429
    assert codes[4] == 429


def test_global_limit_separate_from_auth():
    client = TestClient(_make_app())
    # 认证桶被限流后，普通接口不受影响
    for _ in range(4):
        client.get("/api/auth/ping")
    assert client.get("/api/other").status_code == 200


def test_429_has_chinese_detail():
    client = TestClient(_make_app())
    for _ in range(3):
        client.get("/api/auth/ping")
    r = client.get("/api/auth/ping")
    assert r.status_code == 429
    assert "频繁" in r.json()["detail"]
