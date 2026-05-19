from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.database import Base


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    task_kind = Column(String(20), nullable=False)
    target_mode = Column(String(20), nullable=False)
    target_id = Column(Integer)
    platform = Column(String(20), default="bilibili")
    limit = Column(Integer)
    schedule_type = Column(String(20), nullable=False)
    interval_minutes = Column(Integer)
    daily_time = Column(String(5))
    enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    last_run_at = Column(TIMESTAMP)
    next_run_at = Column(TIMESTAMP)
    last_task_ids = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
