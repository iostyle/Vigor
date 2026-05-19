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
