"""认领申请 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class ClaimOut(BaseModel):
    """认领申请（响应模型）。"""

    id: int
    item_id: int
    applicant_id: int
    applicant_name: str | None = None
    proof_description: str
    proof_images: list[str] = []
    contact: str | None = None
    status: str
    review_comment: str | None = None
    created_at: datetime
    updated_at: datetime
    item_title: str | None = None
    item_type: str | None = None


class ClaimListResponse(BaseModel):
    items: list[ClaimOut]
    total: int
    page: int
    size: int


class ClaimReviewRequest(BaseModel):
    """审核认领申请请求（同意 / 拒绝 / 要求补充证明）。"""

    review_comment: str | None = Field(default=None, max_length=500)
