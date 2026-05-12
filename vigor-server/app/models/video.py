from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint(
            "platform", "external_id", name="uq_videos_platform_external_id"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(16), nullable=False, server_default="douyin", index=True)
    external_id = Column(String(100), nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    title = Column(Text, nullable=False)
    author_name = Column(String(255))
    author_id = Column(String(100))
    cover_url = Column(Text)
    video_url = Column(Text)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    publish_time = Column(TIMESTAMP)
    crawled_at = Column(TIMESTAMP, server_default=func.now())
    last_updated_at = Column(TIMESTAMP)
    heat_score = Column(Float)
    summary = Column(Text)
    summary_generated_at = Column(TIMESTAMP)
    tags = Column(Text)
    status = Column(String(20), nullable=False, default="active", server_default="active", index=True)

    keyword = relationship("Keyword", backref="videos")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
