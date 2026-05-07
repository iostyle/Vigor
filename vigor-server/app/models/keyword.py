from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False)
    category = Column(String(100))
    status = Column(String(20), default="active")
    crawl_threshold = Column(Integer, default=1000)
    priority = Column(Integer, default=5)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
