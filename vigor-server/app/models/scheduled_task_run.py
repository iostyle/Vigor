from sqlalchemy import Column, Integer, String, Text, TIMESTAMP

from app.database import Base


class ScheduledTaskRun(Base):
    __tablename__ = "scheduled_task_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="running")
    started_at = Column(TIMESTAMP, nullable=False)
    finished_at = Column(TIMESTAMP)
    due_count = Column(Integer, nullable=False, default=0)
    dispatched_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    triggered_task_ids = Column(Text)
    error_message = Column(Text)
