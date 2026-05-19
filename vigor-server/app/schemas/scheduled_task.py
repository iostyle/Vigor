from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


ScheduledTaskKind = Literal["crawl", "update"]
ScheduledTargetMode = Literal["category", "keyword", "video"]
ScheduledScheduleType = Literal["interval", "daily"]


class ScheduledTaskBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    task_kind: ScheduledTaskKind
    target_mode: ScheduledTargetMode
    target_id: Optional[int] = Field(default=None, ge=1)
    platform: str = Field(default="bilibili", max_length=20)
    limit: Optional[int] = Field(default=None, ge=1, le=1000)
    schedule_type: ScheduledScheduleType
    interval_minutes: Optional[int] = Field(default=None, ge=5, le=10080)
    daily_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    enabled: bool = True

    @field_validator("daily_time")
    @classmethod
    def validate_daily_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        hour, minute = [int(part) for part in value.split(":")]
        if hour > 23 or minute > 59:
            raise ValueError("daily_time must be HH:mm")
        return value


class ScheduledTaskCreate(ScheduledTaskBase):
    pass


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    task_kind: Optional[ScheduledTaskKind] = None
    target_mode: Optional[ScheduledTargetMode] = None
    target_id: Optional[int] = Field(default=None, ge=1)
    platform: Optional[str] = Field(default=None, max_length=20)
    limit: Optional[int] = Field(default=None, ge=1, le=1000)
    schedule_type: Optional[ScheduledScheduleType] = None
    interval_minutes: Optional[int] = Field(default=None, ge=5, le=10080)
    daily_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    enabled: Optional[bool] = None

    @field_validator("daily_time")
    @classmethod
    def validate_daily_time(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        hour, minute = [int(part) for part in value.split(":")]
        if hour > 23 or minute > 59:
            raise ValueError("daily_time must be HH:mm")
        return value


class ScheduledTaskResponse(BaseModel):
    id: int
    name: str
    task_kind: str
    target_mode: str
    target_id: Optional[int] = None
    platform: Optional[str] = None
    limit: Optional[int] = None
    schedule_type: str
    interval_minutes: Optional[int] = None
    daily_time: Optional[str] = None
    enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_task_ids: list[int] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    target_label: Optional[str] = None

    model_config = {"from_attributes": True}


class ScheduledTaskListResponse(BaseModel):
    total: int
    data: list[ScheduledTaskResponse]


class ScheduledTaskToggle(BaseModel):
    enabled: bool


class SchedulerHealthResponse(BaseModel):
    status: str
    message: str
    seconds_since_last_run: Optional[int] = None


class SchedulerSnapshotResponse(BaseModel):
    last_run_at: Optional[datetime] = None
    last_finished_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_due_count: int = 0
    last_dispatched_count: int = 0
    last_failed_count: int = 0


class ScheduledTaskMonitorStatsResponse(BaseModel):
    enabled_count: int
    disabled_count: int
    due_count: int
    last_24h_total: int
    last_24h_success: int
    last_24h_failed: int
    last_24h_running: int
    source_counts: dict[str, int]


class ScheduledMonitorTaskResponse(BaseModel):
    id: int
    task_type: str
    status: str
    source: str
    source_id: Optional[int] = None
    keyword_id: Optional[int] = None
    videos_crawled: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ScheduledTaskRunResponse(BaseModel):
    id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    due_count: int
    dispatched_count: int
    failed_count: int
    triggered_task_ids: list[int]
    error_message: Optional[str] = None


class ScheduledTaskMonitorResponse(BaseModel):
    server_time: datetime
    health: SchedulerHealthResponse
    scheduler: SchedulerSnapshotResponse
    tasks: ScheduledTaskMonitorStatsResponse
    recent_tasks: list[ScheduledMonitorTaskResponse]
    recent_runs: list[ScheduledTaskRunResponse]
