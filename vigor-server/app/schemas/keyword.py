from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

KeywordStatus = Literal["active", "paused", "archived"]


class KeywordCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    crawl_threshold: int = Field(default=1000, ge=0)
    priority: int = Field(default=5, ge=1, le=10)


class KeywordUpdate(BaseModel):
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    status: Optional[KeywordStatus] = None
    crawl_threshold: Optional[int] = Field(default=None, ge=0)
    priority: Optional[int] = Field(default=None, ge=1, le=10)


class KeywordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    category: Optional[str] = None
    status: str
    crawl_threshold: int
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
