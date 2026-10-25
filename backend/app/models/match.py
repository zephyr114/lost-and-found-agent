"""匹配结果模型。"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class Match(Base):
    """匹配结果表：失物与招领的相似度匹配。"""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lost_item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True, nullable=False)
    found_item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_reason: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)  # new / viewed / dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
