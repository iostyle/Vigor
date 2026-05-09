"""videos 表新增 tags 列(TEXT,存 JSON 字符串)

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-09 15:00:00.000000

Why: 抓取 B 站视频时把 API 返回的 data.tag[].tag_name 落库,
前端在作者行下展示。选 TEXT + JSON 字符串而不是原生 JSON,因为
SQLite 测试环境对 JSON 类型的 API 兼容性差,Postgres 里 TEXT 一样
能读能写,需要查询时再考虑升级列类型。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('tags', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('videos', 'tags')
