from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

KeywordStatus = Literal["active", "paused", "archived"]
# 当前阶段只支持 douyin,后续扩展时在此追加(如 "xhs", "bilibili")
KeywordPlatform = Literal["douyin"]


class KeywordCreate(BaseModel):
    category_id: int = Field(ge=1)
    keyword: str = Field(min_length=1, max_length=255)
    platform: KeywordPlatform = Field(default="douyin")
    crawl_threshold: int = Field(default=1000, ge=0)
    priority: int = Field(default=5, ge=1, le=10)


class KeywordUpdate(BaseModel):
    category_id: Optional[int] = Field(default=None, ge=1)
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    platform: Optional[KeywordPlatform] = None
    status: Optional[KeywordStatus] = None
    crawl_threshold: Optional[int] = Field(default=None, ge=0)
    priority: Optional[int] = Field(default=None, ge=1, le=10)


class KeywordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    keyword: str
    platform: str = "douyin"
    status: str
    crawl_threshold: int
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
