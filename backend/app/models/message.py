"""站内消息模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class Message(Base):
    """消息表：系统通知与用户私信。sender_id 为空表示系统消息。"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    # user / system / claim / match / audit / report / announcement
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
