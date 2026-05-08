"""add platform column to keywords (multi-platform groundwork, phase 1)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-15 10:00:00.000000

迁移逻辑:
1. keywords 表新增 platform 列, VARCHAR(20) NOT NULL DEFAULT 'douyin'
2. 存量数据回填为 'douyin'(由 server_default 自动完成)
3. 该阶段不动 videos/comments 表的 douyin_id 等字段,
   只是给 keyword 加上平台维度,便于后续派发不同平台爬虫。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 新增 platform 列,带 server_default,存量数据自动回填为 'douyin'
    op.add_column(
        'keywords',
        sa.Column(
            'platform',
            sa.String(length=20),
            nullable=False,
            server_default='douyin',
        ),
    )
    # 显式回填一次,确保历史 NULL 值(若有兜底场景)被覆盖
    op.execute("UPDATE keywords SET platform = 'douyin' WHERE platform IS NULL")
    op.create_index('ix_keywords_platform', 'keywords', ['platform'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_keywords_platform', table_name='keywords')
    op.drop_column('keywords', 'platform')
