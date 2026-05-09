"""crawl_tasks 表新增 video_id 列

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-09 18:00:00.000000

Why: 更新任务每条对应一个具体视频,需要记录 video_id 才能在摘要里
显示准确的视频标题,而不是所有任务都显示同一个关键词下的最新标题。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'crawl_tasks',
        sa.Column('video_id', sa.Integer(), sa.ForeignKey('videos.id'), nullable=True),
    )
    op.create_index('ix_crawl_tasks_video_id', 'crawl_tasks', ['video_id'])


def downgrade() -> None:
    op.drop_index('ix_crawl_tasks_video_id', table_name='crawl_tasks')
    op.drop_column('crawl_tasks', 'video_id')
