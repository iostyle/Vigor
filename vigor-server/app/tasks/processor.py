import asyncio
import json
from datetime import datetime

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.comment import Comment, CommentSummary
from app.models.task import CrawlTask
from app.models.video import Video
from app.services.doubao_client import DoubaoClient


def _get_doubao_client() -> DoubaoClient:
    return DoubaoClient(
        api_key=settings.DOUBAO_API_KEY,
        mock_mode=settings.DOUBAO_MOCK_MODE,
    )


def _load_top_comments(db, video_id: int) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.video_id == video_id)
        .order_by(Comment.like_count.desc())
        .limit(50)
        .all()
    )


@celery_app.task(
    name="app.tasks.processor.generate_summary",
    queue="processor",
    bind=True,
    max_retries=5,
    default_retry_delay=30,
)
def generate_summary_task(self, video_id: int, task_id: int | None = None):
    """为指定视频生成摘要(视频摘要 + 评论摘要)。

    如果 DB 里没有评论但 video.comment_count > 0,先同步等一次
    crawl_video_comments 把评论补到库里,再生成摘要。

    task_id: 由 admin/videos.trigger_generate_summary 预创建的 CrawlTask
    行 ID,传入时复用该行写 running/success/failed + 时间戳;自动派发
    (比如 crawler 里完成后 .delay(video.id))不传 task_id,不创建任务行。
    """
    db = SessionLocal()
    task_record: CrawlTask | None = None
    if task_id is not None:
        task_record = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
    if task_record is not None:
        task_record.status = "running"
        task_record.started_at = datetime.utcnow()
        db.add(task_record)
        db.commit()

    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            if task_record is not None:
                task_record.status = "failed"
                task_record.error_message = f"Video {video_id} not found"
                task_record.completed_at = datetime.utcnow()
                db.add(task_record)
                db.commit()
            return {"status": "error", "message": f"Video {video_id} not found"}

        comments = _load_top_comments(db, video_id)

        # Why: 用户在详情页点"生成摘要"时,如果评论还没入库会什么都不发生
        # 这里先补抓一次,爬完再走后续摘要生成。crawl 失败也继续走(只是没评论而已)
        if not comments and (video.comment_count or 0) > 0:
            # 延迟 import,避免循环依赖
            from app.tasks.crawler import crawl_video_comments

            crawl_result = crawl_video_comments.apply_async(
                args=(video_id,), queue="crawler"
            )
            try:
                # disable_sync_subtasks=False:允许在 task 内等子 task
                # 我们用独立 queue + 足够并发,不会死锁
                crawl_result.get(timeout=60, disable_sync_subtasks=False)
            except Exception:
                # 超时或失败都不阻断,后面再次查评论,可能有也可能没有
                pass

            db.expire_all()
            comments = _load_top_comments(db, video_id)

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

        if task_record is not None:
            task_record.status = "success"
            task_record.videos_crawled = 1
            task_record.completed_at = datetime.utcnow()
            db.add(task_record)

        db.commit()
        return {"status": "success", "video_id": video_id}

    except Exception as exc:
        db.rollback()
        if task_record is not None:
            try:
                task_record.status = "failed"
                task_record.error_message = str(exc)[:500]
                task_record.completed_at = datetime.utcnow()
                db.add(task_record)
                db.commit()
            except Exception:
                db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
