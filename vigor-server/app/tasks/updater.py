import asyncio
from datetime import datetime, timedelta

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.video import Video
from app.services.douyin_client import DouyinClient
from app.services.heat_calculator import calculate_heat_score


def _get_douyin_client() -> DouyinClient:
    return DouyinClient(
        api_key=settings.DOUYIN_API_KEY,
        mock_mode=settings.DOUYIN_MOCK_MODE,
        base_url=settings.DOUYIN_API_BASE_URL,
        max_concurrency=settings.DOUYIN_MAX_CONCURRENCY,
    )


def _is_due_for_update(video: Video, now: datetime) -> bool:
    last_updated_at = video.last_updated_at or video.crawled_at or datetime.min
    heat_score = video.heat_score or 0.0

    if heat_score > 10000:
        interval = timedelta(hours=1)
    elif heat_score >= 1000:
        interval = timedelta(hours=6)
    else:
        interval = timedelta(hours=24)

    return last_updated_at <= now - interval


@celery_app.task(
    name="app.tasks.updater.update_videos",
    queue="updater",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_videos_task(self):
    db = SessionLocal()
    try:
        now = datetime.now()
        client = _get_douyin_client()
        updated_count = 0
        comment_crawl_count = 0

        videos = db.query(Video).all()
        due_videos = [video for video in videos if _is_due_for_update(video, now)]

        for video in due_videos:
            old_comment_count = video.comment_count or 0
            detail = asyncio.run(client.get_video_detail(video.douyin_id))

            video.like_count = detail.get("like_count", 0)
            video.comment_count = detail.get("comment_count", 0)
            video.share_count = detail.get("share_count", 0)
            video.heat_score = calculate_heat_score(
                video.like_count,
                video.comment_count,
                video.share_count,
                video.publish_time,
            )
            video.last_updated_at = now
            updated_count += 1

            if old_comment_count > 0 and video.comment_count > old_comment_count * 1.2:
                celery_app.send_task(
                    "app.tasks.crawler.crawl_video_comments",
                    args=[video.id],
                    queue="crawler",
                )
                comment_crawl_count += 1

        db.commit()
        return {
            "status": "success",
            "updated_count": updated_count,
            "comment_crawl_count": comment_crawl_count,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
