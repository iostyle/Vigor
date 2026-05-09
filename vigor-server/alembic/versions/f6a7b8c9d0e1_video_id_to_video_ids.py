"""crawl_tasks: video_id → video_ids (TEXT JSON 数组,支持多视频)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-09 19:00:00.000000

Why: 用户建议用 video_ids 存多个视频 ID,爬取任务存所有爬到的视频 ID,
更新任务存要更新的视频 ID。比单个 video_id 更灵活。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新增 video_ids TEXT 列(存 JSON 数组)
    op.add_column(
        'crawl_tasks',
        sa.Column('video_ids', sa.Text(), nullable=True),
    )
    # 把已有 video_id 数据迁移到 video_ids(单元素数组)
    op.execute(
        "UPDATE crawl_tasks SET video_ids = '[' || video_id || ']' "
        "WHERE video_id IS NOT NULL"
    )
    # 删除旧 video_id 列
    op.drop_index('ix_crawl_tasks_video_id', table_name='crawl_tasks')
    op.drop_column('crawl_tasks', 'video_id')


def downgrade() -> None:
    op.add_column(
        'crawl_tasks',
        sa.Column('video_id', sa.Integer(), sa.ForeignKey('videos.id'), nullable=True),
    )
    op.create_index('ix_crawl_tasks_video_id', 'crawl_tasks', ['video_id'])
    # 从 video_ids 取第一个元素回填
    op.execute(
        "UPDATE crawl_tasks SET video_id = "
        "CAST(TRIM(BOTH '[]' FROM SPLIT_PART(video_ids, ',', 1)) AS INTEGER) "
        "WHERE video_ids IS NOT NULL AND video_ids != '[]'"
    )
    op.drop_column('crawl_tasks', 'video_ids')
