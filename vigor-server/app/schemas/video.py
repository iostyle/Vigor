from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.comment import CommentSummaryResponse


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    douyin_id: str
    title: str
    author_name: Optional[str] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    heat_score: Optional[float] = None
    publish_time: Optional[datetime] = None
    summary: Optional[str] = None
    comment_summary: Optional[CommentSummaryResponse] = None


class VideoListResponse(BaseModel):
    total: int = Field(ge=0)
    data: list[VideoResponse]
