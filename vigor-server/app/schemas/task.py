from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

CrawlTaskStatus = Literal["pending", "running", "success", "failed"]


def _as_utc(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class CrawlTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword_id: Optional[int] = None
    video_ids: list[int] = []
    task_type: str
    status: CrawlTaskStatus
    videos_crawled: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None

    @field_validator("video_ids", mode="before")
    @classmethod
    def _parse_video_ids(cls, value):
        """DB 里是 TEXT(JSON 字符串),解析成 list[int]。"""
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(x) for x in value if x is not None]
        if isinstance(value, str):
            import json as _json
            try:
                parsed = _json.loads(value)
            except (ValueError, TypeError):
                return []
            if isinstance(parsed, list):
                return [int(x) for x in parsed if x is not None]
        return []

    @field_serializer("started_at", "completed_at")
    def _ser_dt(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc(value)
