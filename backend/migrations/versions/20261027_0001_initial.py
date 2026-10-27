"""初始建表（与当前 ORM 模型保持一致）。

Revision ID: 20261027_0001
Revises:
Create Date: 2026-10-27
"""

from alembic import op

import app.models  # noqa: F401  注册全部模型
from app.database.session import Base

revision = "20261027_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """使用模型元数据创建全部表（初始迁移）。"""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
