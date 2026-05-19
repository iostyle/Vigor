"""add scheduled task runs

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-05-19 18:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("scheduled_task_runs"):
        op.create_table(
            "scheduled_task_runs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("started_at", sa.TIMESTAMP(), nullable=False),
            sa.Column("finished_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("due_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("dispatched_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("triggered_task_ids", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("scheduled_task_runs")}
    if "ix_scheduled_task_runs_started_at" not in index_names:
        op.create_index(
            "ix_scheduled_task_runs_started_at",
            "scheduled_task_runs",
            ["started_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("scheduled_task_runs"):
        index_names = {idx["name"] for idx in inspector.get_indexes("scheduled_task_runs")}
        if "ix_scheduled_task_runs_started_at" in index_names:
            op.drop_index("ix_scheduled_task_runs_started_at", table_name="scheduled_task_runs")
        op.drop_table("scheduled_task_runs")
