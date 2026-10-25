"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, announcements, auth, claims, health, items, matches, messages, reports, users
from app.core.config import settings
from app.core.security import hash_password
from app.database.session import Base, SessionLocal, engine
from app.models import User

# 上传文件静态目录：backend/uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent / settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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
app.include_router(reports.router, prefix="/api")
app.include_router(announcements.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# 上传的图片通过 /uploads/... 访问
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
