"""限流计数模型：存数据库，Serverless 多实例下也生效。"""

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class RateLimitCounter(Base):
    """按（IP+分类, 时间窗）累计请求数。"""

    __tablename__ = "rate_limit_counters"

    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    window_start: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
