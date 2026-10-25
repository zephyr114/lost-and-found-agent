"""公告 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    status: str
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
