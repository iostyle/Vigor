from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Keyword(Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("category_id", "keyword", name="uq_keywords_category_keyword"),
    )

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    crawl_threshold = Column(Integer, default=1000)
    priority = Column(Integer, default=5)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", backref="keywords")
