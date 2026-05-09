from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.schemas.comment import CommentSummaryResponse


def _as_utc(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    platform: str = "douyin"
    title: str
    author_name: Optional[str] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    heat_score: Optional[float] = None
    publish_time: Optional[datetime] = None
    crawled_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    comment_summary: Optional[CommentSummaryResponse] = None

    @field_serializer("publish_time", "crawled_at", "last_updated_at")
    def _ser_dt(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc(value)


class VideoListResponse(BaseModel):
    total: int = Field(ge=0)
    data: list[VideoResponse]
