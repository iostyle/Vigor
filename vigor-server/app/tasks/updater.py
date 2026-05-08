import asyncio
from datetime import datetime, timedelta

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.keyword import Keyword
from app.models.video import Video
from app.services.heat_calculator import calculate_heat_score
from app.services.platform_client import get_client


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
        updated_count = 0
        comment_crawl_count = 0

        videos = db.query(Video).all()
        due_videos = [video for video in videos if _is_due_for_update(video, now)]

        # Why: 同一次 tick 内缓存按 platform 的 client,避免每个视频都重建
        client_cache: dict[str, object] = {}

        for video in due_videos:
            kw = (
                db.query(Keyword).filter(Keyword.id == video.keyword_id).first()
                if video.keyword_id
                else None
            )
            platform = (getattr(kw, "platform", None) or "douyin").lower()
            client = client_cache.get(platform)
            if client is None:
                client = get_client(platform)
                client_cache[platform] = client

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
