"""Agent 执行日志模型。"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.user import utcnow


class AgentLog(Base):
    """Agent 执行日志表：记录工具调用与结果。"""

    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # item_matching / attribute_extract ...
    input_data: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_result: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)  # success / failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
