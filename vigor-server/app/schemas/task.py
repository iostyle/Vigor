from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

CrawlTaskStatus = Literal["pending", "running", "success", "failed"]


class CrawlTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword_id: Optional[int] = None
    task_type: str
    status: CrawlTaskStatus
    videos_crawled: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
