"""物品相关 Pydantic 模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """发布失物 / 招领请求。"""

    item_type: Literal["lost", "found"]
    title: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, max_length=30)
    brand: str | None = Field(default=None, max_length=50)
    location: str = Field(min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    event_time: datetime


class ItemUpdate(BaseModel):
    """编辑物品请求（仅更新传入字段）。"""

    title: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, max_length=30)
    brand: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    event_time: datetime | None = None


class ItemOut(BaseModel):
    """物品信息（响应模型）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    item_type: str
    title: str
    category: str
    description: str | None = None
    color: str | None = None
    brand: str | None = None
    location: str
    latitude: float | None = None
    longitude: float | None = None
    event_time: datetime
    images: list[str] = []
    status: str
    audit_status: str
    created_at: datetime
    updated_at: datetime
    username: str | None = None


class ItemListResponse(BaseModel):
    """物品列表响应。"""

    items: list[ItemOut]
    total: int
    page: int
    size: int
