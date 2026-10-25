"""消息 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class MessageSendRequest(BaseModel):
    receiver_id: int
    content: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    id: int
    sender_id: int | None = None
    sender_name: str | None = None
    receiver_id: int
    message_type: str
    content: str
    is_read: bool
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageOut]
    total: int
    page: int
    size: int
