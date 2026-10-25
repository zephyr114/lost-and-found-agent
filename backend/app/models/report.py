"""举报模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class Report(Base):
    """举报表：用户举报虚假信息、恶意认领、违规内容等。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # item / user / claim
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending / handled / dismissed
    handler_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    handler_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
