"""add task source

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-19 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("crawl_tasks")}

    if "source" not in columns:
        op.add_column(
            "crawl_tasks",
            sa.Column("source", sa.String(length=20), nullable=True),
        )
    if "source_id" not in columns:
        op.add_column(
            "crawl_tasks",
            sa.Column("source_id", sa.Integer(), nullable=True),
        )

    op.execute("UPDATE crawl_tasks SET source = 'legacy' WHERE source IS NULL OR source = ''")

    index_names = {idx["name"] for idx in inspector.get_indexes("crawl_tasks")}
    if "ix_crawl_tasks_source" not in index_names:
        op.create_index("ix_crawl_tasks_source", "crawl_tasks", ["source", "source_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    index_names = {idx["name"] for idx in inspector.get_indexes("crawl_tasks")}
    if "ix_crawl_tasks_source" in index_names:
        op.drop_index("ix_crawl_tasks_source", table_name="crawl_tasks")

    columns = {col["name"] for col in inspector.get_columns("crawl_tasks")}
    if "source_id" in columns:
        op.drop_column("crawl_tasks", "source_id")
    if "source" in columns:
        op.drop_column("crawl_tasks", "source")
