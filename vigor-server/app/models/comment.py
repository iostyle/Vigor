from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "external_comment_id",
            name="uq_comments_platform_external_comment_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    platform = Column(String(16), nullable=False, server_default="douyin", index=True)
    external_comment_id = Column(String(100))
    author_name = Column(String(255))
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    publish_time = Column(TIMESTAMP)
    crawled_at = Column(TIMESTAMP, server_default=func.now())

    video = relationship("Video", back_populates="comments")


class CommentSummary(Base):
    __tablename__ = "comment_summaries"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True)
    summary = Column(Text)
    top_keywords = Column(Text)
    sentiment = Column(String(20))
    generated_at = Column(TIMESTAMP, server_default=func.now())
    comment_count = Column(Integer)
