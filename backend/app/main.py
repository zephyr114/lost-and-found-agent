"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 第一阶段暂无数据表需要初始化；
    # 后续阶段在此执行建表 / 迁移（Alembic）
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

# /health 挂载在根路径（验收标准）；业务接口后续统一挂载到 /api 前缀
app.include_router(health.router)
