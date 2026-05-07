from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Sentiment = Literal["positive", "neutral", "negative", "mixed"]


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author_name: Optional[str] = None
    like_count: int = 0
    publish_time: Optional[datetime] = None


class CommentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    summary: str
    top_keywords: list[str] = Field(default_factory=list)
    sentiment: Sentiment
    generated_at: datetime
    comment_count: int = Field(ge=0)
