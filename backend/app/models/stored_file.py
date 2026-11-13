"""上传文件模型：图片等小文件直接存数据库，避免 Serverless 临时目录丢失。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class StoredFile(Base):
    """数据库中的二进制文件（图片等）。"""

    __tablename__ = "stored_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
