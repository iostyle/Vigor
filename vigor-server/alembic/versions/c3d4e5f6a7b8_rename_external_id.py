"""videos/comments 表增加 platform 列,重命名 external_id,删除 keywords.platform

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-08 17:00:00.000000

Why: 修正 Phase 1 的设计错误
- 关键词应该跟平台正交(同一个"股票"关键词既能爬抖音也能爬 B 站)
- platform 是视频实例的属性,不是关键词的属性
- 平台是触发爬取时的参数,应该存储在 videos/comments 表中

What:
1. 删除 keywords.platform 列(包括索引 ix_keywords_platform)
2. videos 表:
   - douyin_id → external_id (重命名列和索引)
   - 新增 platform 列 (VARCHAR(16) NOT NULL DEFAULT 'douyin')
   - 回填历史数据 platform='douyin'
   - 唯一约束改为 (platform, external_id) 复合唯一
3. comments 表:
   - douyin_comment_id → external_comment_id (重命名列和约束)
   - 新增 platform 列 (VARCHAR(16) NOT NULL DEFAULT 'douyin')
   - 回填历史数据 platform='douyin'
   - 唯一约束改为 (platform, external_comment_id) 复合唯一
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== 1. 删除 keywords.platform 列 ==========
    op.drop_index('ix_keywords_platform', table_name='keywords')
    op.drop_column('keywords', 'platform')

    # ========== 2. videos 表改造 ==========
    # 2.1 重命名列: douyin_id → external_id
    op.alter_column('videos', 'douyin_id', new_column_name='external_id')

    # 2.2 删除旧的单列唯一索引
    op.drop_index('ix_videos_douyin_id', table_name='videos')

    # 2.3 新增 platform 列
    op.add_column(
        'videos',
        sa.Column(
            'platform',
            sa.String(length=16),
            nullable=False,
            server_default='douyin',
        ),
    )
    # 回填历史数据
    op.execute("UPDATE videos SET platform = 'douyin' WHERE platform IS NULL")
    op.create_index('ix_videos_platform', 'videos', ['platform'])

    # 2.4 创建复合唯一约束 (platform, external_id)
    op.create_unique_constraint(
        'uq_videos_platform_external_id',
        'videos',
        ['platform', 'external_id']
    )

    # ========== 3. comments 表改造 ==========
    # 3.1 重命名列: douyin_comment_id → external_comment_id
    op.alter_column('comments', 'douyin_comment_id', new_column_name='external_comment_id')

    # 3.2 删除旧的单列唯一约束
    op.drop_constraint('comments_douyin_comment_id_key', 'comments', type_='unique')

    # 3.3 新增 platform 列
    op.add_column(
        'comments',
        sa.Column(
            'platform',
            sa.String(length=16),
            nullable=False,
            server_default='douyin',
        ),
    )
    # 回填历史数据
    op.execute("UPDATE comments SET platform = 'douyin' WHERE platform IS NULL")
    op.create_index('ix_comments_platform', 'comments', ['platform'])

    # 3.4 创建复合唯一约束 (platform, external_comment_id)
    op.create_unique_constraint(
        'uq_comments_platform_external_comment_id',
        'comments',
        ['platform', 'external_comment_id']
    )


def downgrade() -> None:
    # ========== 3. comments 表回滚 ==========
    op.drop_constraint('uq_comments_platform_external_comment_id', 'comments', type_='unique')
    op.drop_index('ix_comments_platform', table_name='comments')
    op.drop_column('comments', 'platform')
    op.create_unique_constraint(
        'comments_douyin_comment_id_key',
        'comments',
        ['external_comment_id']
    )
    op.alter_column('comments', 'external_comment_id', new_column_name='douyin_comment_id')

    # ========== 2. videos 表回滚 ==========
    op.drop_constraint('uq_videos_platform_external_id', 'videos', type_='unique')
    op.drop_index('ix_videos_platform', table_name='videos')
    op.drop_column('videos', 'platform')
    op.create_index('ix_videos_douyin_id', 'videos', ['external_id'], unique=True)
    op.alter_column('videos', 'external_id', new_column_name='douyin_id')

    # ========== 1. keywords.platform 列恢复 ==========
    op.add_column(
        'keywords',
        sa.Column(
            'platform',
            sa.String(length=20),
            nullable=False,
            server_default='douyin',
        ),
    )
    op.create_index('ix_keywords_platform', 'keywords', ['platform'])
