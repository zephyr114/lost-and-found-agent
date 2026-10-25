"""认领申请模型。"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class Claim(Base):
    """认领申请表：申请人对招领物品发起认领，由物品发布者处理。"""

    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True, nullable=False)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    proof_description: Mapped[str] = mapped_column(Text, nullable=False)
    proof_images: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending/approved/rejected/need_more_proof/cancelled
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
