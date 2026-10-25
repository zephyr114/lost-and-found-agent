"""举报 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    """用户提交举报。"""

    target_type: str = Field(pattern="^(item|user|claim)$")
    target_id: int
    reason: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ReportOut(BaseModel):
    id: int
    reporter_id: int
    reporter_name: str | None = None
    target_type: str
    target_id: int
    reason: str
    description: str | None = None
    status: str
    handler_id: int | None = None
    handler_comment: str | None = None
    created_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportOut]
    total: int
    page: int
    size: int


class HandleReportRequest(BaseModel):
    """管理员处理举报。"""

    action: str = Field(pattern="^(handled|dismissed)$")
    comment: str | None = Field(default=None, max_length=500)
