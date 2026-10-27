"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, agent, announcements, auth, claims, health, items, matches, messages, reports, stats, users
from app.core.config import settings
from app.core.ratelimit import RateLimitMiddleware
from app.core.security import hash_password
from app.database.session import Base, SessionLocal, engine
from app.models import User

# 上传文件静态目录：backend/uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent / settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 前端构建产物（单镜像部署时由 Docker 拷贝到 backend/frontend_dist）
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"


def seed_admin() -> None:
    """首次启动时创建初始管理员账号（账号密码见 .env 的 ADMIN_* 配置）。"""
    db = SessionLocal()
    try:
        exists = (
            db.query(User)
            .filter((User.username == settings.admin_username) | (User.email == settings.admin_email))
            .first()
        )
        if exists:
            return
        db.add(
            User(
                username=settings.admin_username,
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
                status="active",
                credit_score=100,
            )
        )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 开发阶段直接建表（后续引入 Alembic 迁移）
    Base.metadata.create_all(bind=engine)
    seed_admin()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="失物招领智能平台后端服务",
    lifespan=lifespan,
)

# 限流：按 IP 限制 /api 请求（认证接口更严格）；测试环境可通过 RATE_LIMIT_ENABLED=false 关闭
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        auth_limit=settings.rate_limit_auth_per_minute,
        global_limit=settings.rate_limit_global_per_minute,
    )

# CORS：通配符时不允许携带凭据，显式来源列表时才允许
_origins = settings.cors_origin_list
if "*" in _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# /health 挂载在根路径（第一阶段验收）；业务接口统一挂载到 /api 前缀
app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(announcements.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# 上传的图片通过 /uploads/... 访问
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 单镜像部署（如 Hugging Face Spaces）时，由 FastAPI 同时托管前端 SPA
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str):
        if path.startswith(("api/", "uploads/", "docs", "redoc", "openapi.json", "health")):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
