"""add platform to crawl tasks

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-05-21 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crawl_tasks")}

    if "platform" not in columns:
        op.add_column(
            "crawl_tasks",
            sa.Column("platform", sa.String(length=20), nullable=True),
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("crawl_tasks")}
    if "ix_crawl_tasks_platform" not in index_names:
        op.create_index("ix_crawl_tasks_platform", "crawl_tasks", ["platform"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    index_names = {idx["name"] for idx in inspector.get_indexes("crawl_tasks")}
    if "ix_crawl_tasks_platform" in index_names:
        op.drop_index("ix_crawl_tasks_platform", table_name="crawl_tasks")

    columns = {col["name"] for col in inspector.get_columns("crawl_tasks")}
    if "platform" in columns:
        op.drop_column("crawl_tasks", "platform")
