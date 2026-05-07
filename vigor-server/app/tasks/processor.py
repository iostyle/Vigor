import asyncio
import json
from datetime import datetime

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.comment import Comment, CommentSummary
from app.models.video import Video
from app.services.doubao_client import DoubaoClient


def _get_doubao_client() -> DoubaoClient:
    return DoubaoClient(
        api_key=settings.DOUBAO_API_KEY,
        mock_mode=settings.DOUBAO_MOCK_MODE,
    )


@celery_app.task(
    name="app.tasks.processor.generate_summary",
    queue="processor",
    bind=True,
    max_retries=5,
    default_retry_delay=30,
)
def generate_summary_task(self, video_id: int):
    """为指定视频生成摘要(视频摘要 + 评论摘要)"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": f"Video {video_id} not found"}

        comments = (
            db.query(Comment)
            .filter(Comment.video_id == video_id)
            .order_by(Comment.like_count.desc())
            .limit(50)
            .all()
        )

        client = _get_doubao_client()

        video_summary = asyncio.run(
            client.generate_video_summary(video.title)
        )
        video.summary = video_summary
        video.summary_generated_at = datetime.now()

        if comments:
            comment_texts = [c.content for c in comments]
            comment_result = asyncio.run(
                client.generate_comment_summary(comment_texts)
            )

            existing = (
                db.query(CommentSummary)
                .filter(CommentSummary.video_id == video_id)
                .first()
            )
            if existing:
                existing.summary = comment_result.get("summary", "")
                existing.sentiment = comment_result.get("sentiment", "neutral")
                existing.top_keywords = json.dumps(
                    comment_result.get("top_keywords", []), ensure_ascii=False
                )
                existing.generated_at = datetime.now()
                existing.comment_count = len(comments)
            else:
                cs = CommentSummary(
                    video_id=video_id,
                    summary=comment_result.get("summary", ""),
                    sentiment=comment_result.get("sentiment", "neutral"),
                    top_keywords=json.dumps(
                        comment_result.get("top_keywords", []), ensure_ascii=False
                    ),
                    generated_at=datetime.now(),
                    comment_count=len(comments),
                )
                db.add(cs)

        db.commit()
        return {"status": "success", "video_id": video_id}

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
