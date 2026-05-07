from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class CrawlTask(Base):
    __tablename__ = "crawl_tasks"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    task_type = Column(String(50))
    status = Column(String(20))
    videos_crawled = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
