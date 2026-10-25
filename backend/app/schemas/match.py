"""智能匹配 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """对指定物品运行匹配分析。"""

    item_id: int


class MatchOut(BaseModel):
    id: int
    lost_item_id: int
    found_item_id: int
    match_score: float
    match_reason: list[str] = []
    status: str
    created_at: datetime
    lost_title: str | None = None
    found_title: str | None = None


class MatchListResponse(BaseModel):
    items: list[MatchOut]
    total: int
