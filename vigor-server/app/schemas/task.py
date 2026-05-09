from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_serializer

CrawlTaskStatus = Literal["pending", "running", "success", "failed"]


def _as_utc(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    # 用 Z 尾缀,前端 new Date() 可准确按本地时区渲染
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class CrawlTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword_id: Optional[int] = None
    video_id: Optional[int] = None
    task_type: str
    status: CrawlTaskStatus
    videos_crawled: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None

    @field_serializer("started_at", "completed_at")
    def _ser_dt(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc(value)
