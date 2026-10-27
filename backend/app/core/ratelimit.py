"""简单内存限流中间件：按 IP + 分类滑动窗口计数（无需 Redis，单进程有效）。"""

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """对 /api 请求按 IP 限流；认证接口使用更严格的限额。"""

    def __init__(self, app: FastAPI, auth_limit: int = 30, global_limit: int = 300, window_seconds: int = 60):
        super().__init__(app)
        self.auth_limit = auth_limit
        self.global_limit = global_limit
        self.window = window_seconds
        self.buckets: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            is_auth = path.startswith("/api/auth/")
            limit = self.auth_limit if is_auth else self.global_limit
            key = f"{ip}:{'auth' if is_auth else 'global'}"
            bucket = [t for t in self.buckets.get(key, []) if now - t < self.window]
            if len(bucket) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "请求过于频繁，请稍后再试"},
                )
            bucket.append(now)
            self.buckets[key] = bucket
            # 防止内存无限增长
            if len(self.buckets) > 10000:
                self.buckets = {
                    k: v for k, v in self.buckets.items() if any(now - t < self.window for t in v)
                }
        return await call_next(request)
