"""add scheduled tasks

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-19 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("scheduled_tasks"):
        op.create_table(
            "scheduled_tasks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("task_kind", sa.String(length=20), nullable=False),
            sa.Column("target_mode", sa.String(length=20), nullable=False),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("platform", sa.String(length=20), nullable=True),
            sa.Column("limit", sa.Integer(), nullable=True),
            sa.Column("schedule_type", sa.String(length=20), nullable=False),
            sa.Column("interval_minutes", sa.Integer(), nullable=True),
            sa.Column("daily_time", sa.String(length=5), nullable=True),
            sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("last_run_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("next_run_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("last_task_ids", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("scheduled_tasks")}
    if "ix_scheduled_tasks_id" not in index_names:
        op.create_index("ix_scheduled_tasks_id", "scheduled_tasks", ["id"])
    if "ix_scheduled_tasks_enabled_next_run" not in index_names:
        op.create_index(
            "ix_scheduled_tasks_enabled_next_run",
            "scheduled_tasks",
            ["enabled", "next_run_at"],
        )


def downgrade() -> None:
    op.drop_index("ix_scheduled_tasks_enabled_next_run", table_name="scheduled_tasks")
    op.drop_index("ix_scheduled_tasks_id", table_name="scheduled_tasks")
    op.drop_table("scheduled_tasks")
