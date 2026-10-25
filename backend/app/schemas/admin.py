"""管理端 Pydantic 模型。"""

from pydantic import BaseModel, Field


class StatisticsOut(BaseModel):
    users_total: int
    users_active: int
    users_disabled: int
    items_total: int
    items_lost: int
    items_found: int
    items_pending_audit: int
    items_claimed: int
    claims_total: int
    claims_pending: int
    matches_total: int
    reports_pending: int
    announcements_active: int


class AuditItemRequest(BaseModel):
    """审核物品请求。"""

    decision: str = Field(pattern="^(approve|reject)$")
    comment: str | None = Field(default=None, max_length=500)


class UserStatusRequest(BaseModel):
    """修改用户状态请求。"""

    status: str = Field(pattern="^(active|disabled)$")


class HandleReportRequest(BaseModel):
    action: str = Field(pattern="^(handled|dismissed)$")
    comment: str | None = Field(default=None, max_length=500)
