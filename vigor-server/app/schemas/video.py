from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

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
    status: str = "active"
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
    tags: list[str] = Field(default_factory=list)
    comment_summary: Optional[CommentSummaryResponse] = None

    @field_serializer("publish_time", "crawled_at", "last_updated_at")
    def _ser_dt(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc(value)

    @field_validator("tags", mode="before")
    @classmethod
    def _parse_tags(cls, value):
        """DB 里是 TEXT(JSON 字符串),客户端可以传 list;都收成 list[str]。"""
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(x) for x in value]
        if isinstance(value, str):
            import json as _json

            try:
                parsed = _json.loads(value)
            except (ValueError, TypeError):
                return []
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        return []


class VideoListResponse(BaseModel):
    total: int = Field(ge=0)
    data: list[VideoResponse]
