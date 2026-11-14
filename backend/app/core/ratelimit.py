"""分布式限流中间件：用数据库（Neon）做计数，多实例 / Serverless 下同样生效。

设计：
- 按（IP + 分类 + 时间窗）在 rate_limit_counters 表中累加
- 使用 INSERT ... ON CONFLICT DO UPDATE ... RETURNING 保证原子性
- 数据库异常时「失败放行」，不影响正常请求
"""

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from app.database.session import engine

_INCREMENT_SQL = text(
    """
    INSERT INTO rate_limit_counters ("key", window_start, count)
    VALUES (:k, :w, 1)
    ON CONFLICT ("key", window_start)
    DO UPDATE SET count = rate_limit_counters.count + 1
    RETURNING count
    """
)

_CLEANUP_SQL = text("DELETE FROM rate_limit_counters WHERE window_start < :old")


def _hit(key: str, window: int, limit: int) -> int | None:
    """累加并返回当前窗口计数；异常返回 None（放行）。"""
    try:
        with engine.begin() as conn:
            current = conn.execute(_INCREMENT_SQL, {"k": key, "w": window}).scalar()
            # 偶发清理过期窗口，避免表无限增长
            if current == 1:
                conn.execute(_CLEANUP_SQL, {"old": window - 10})
        return int(current) if current is not None else None
    except Exception:
        return None


def _client_ip(request: Request) -> str:
    """取真实客户端 IP：优先 Cloudflare 头，其次 X-Forwarded-For，最后 socket 地址。"""
    cf = request.headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """对 /api 请求按 IP 限流；认证接口使用更严格的限额。"""

    def __init__(self, app: FastAPI, auth_limit: int = 30, global_limit: int = 300, window_seconds: int = 60):
        super().__init__(app)
        self.auth_limit = auth_limit
        self.global_limit = global_limit
        self.window = window_seconds

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            ip = _client_ip(request)
            is_auth = path.startswith("/api/auth/")
            limit = self.auth_limit if is_auth else self.global_limit
            window = int(time.time()) // self.window
            key = f"{ip}:{'auth' if is_auth else 'global'}"

            current = await run_in_threadpool(_hit, key, window, limit)
            if current is not None and current > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                )
        return await call_next(request)
