import asyncio
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.task import CrawlTask
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


def _refresh_videos(
    db: Session, videos: list[Video], now: datetime
) -> tuple[int, int]:
    """强制刷新一批视频的点赞/评论/分享/热度,不判断时间窗口。

    被 beat 的 update_videos_task(在外层先做时间窗口过滤)和
    手动 update_selection_task(直接传选中视频)共用。

    返回 (updated_count, comment_crawl_count)。
    评论数 >20% 增长会派发 crawl_video_comments 子任务。

    单条视频遇到平台业务侧"不可见/不存在"(detail 返回 unavailable=True)
    时跳过更新指标,只把 last_updated_at 推进,不计入 updated_count;
    整批继续,不让一条下架视频拖垮整批。
    """
    updated_count = 0
    comment_crawl_count = 0

    # Why: 缓存按 platform 的 client,避免每个视频都重建
    client_cache: dict[str, object] = {}

    for video in videos:
        platform = (video.platform or "douyin").lower()
        client = client_cache.get(platform)
        if client is None:
            client = get_client(platform)
            client_cache[platform] = client

        old_comment_count = video.comment_count or 0
        detail = asyncio.run(client.get_video_detail(video.external_id))

        if detail.get("unavailable"):
            # 稿件已下架/不可见,跳过指标更新,但推进 last_updated_at
            # 防止下次 beat 又把它选进来无限重试
            video.last_updated_at = now
            continue

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
        # tags 也同步更新,detail 有就覆盖,没有就不动
        detail_tags = detail.get("tags")
        if detail_tags is not None:
            video.tags = json.dumps(detail_tags or [], ensure_ascii=False)
        updated_count += 1

        if old_comment_count > 0 and video.comment_count > old_comment_count * 1.2:
            celery_app.send_task(
                "app.tasks.crawler.crawl_video_comments",
                args=[video.id],
                queue="crawler",
            )
            comment_crawl_count += 1

    return updated_count, comment_crawl_count


@celery_app.task(
    name="app.tasks.updater.update_videos",
    queue="updater",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_videos_task(self):
    """beat 触发的全表扫描,按 _is_due_for_update 过滤后刷新。"""
    db = SessionLocal()
    try:
        now = datetime.now()
        videos = db.query(Video).all()
        due_videos = [v for v in videos if _is_due_for_update(v, now)]

        updated_count, comment_crawl_count = _refresh_videos(db, due_videos, now)

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


@celery_app.task(
    name="app.tasks.updater.update_selection",
    queue="updater",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def update_selection_task(
    self,
    video_id: int | None = None,
    keyword_id: int | None = None,
    task_id: int | None = None,
):
    """手动触发:刷新指定 video 或某关键词下所有视频,跳过时间窗口判断。

    复用 trigger_update API 预创建的 CrawlTask 行(传 task_id),
    把 status pending → running → success/failed,写入 started_at/
    completed_at/videos_crawled/error_message,避免出现两条记录。
    """
    db = SessionLocal()
    task_record: CrawlTask | None = None
    try:
        if task_id is not None:
            task_record = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if task_record is not None:
            task_record.status = "running"
            task_record.started_at = datetime.utcnow()
            db.add(task_record)
            db.commit()

        # 选中视频集合:优先 video_id,其次 keyword_id
        if video_id is not None:
            videos = db.query(Video).filter(Video.id == video_id).all()
        elif keyword_id is not None:
            videos = db.query(Video).filter(Video.keyword_id == keyword_id).all()
        else:
            videos = []

        now = datetime.utcnow()
        updated_count, comment_crawl_count = _refresh_videos(db, videos, now)

        if task_record is not None:
            task_record.status = "success"
            task_record.videos_crawled = updated_count
            task_record.error_message = None
            task_record.completed_at = datetime.utcnow()
            db.add(task_record)

        db.commit()
        return {
            "status": "success",
            "video_id": video_id,
            "keyword_id": keyword_id,
            "updated_count": updated_count,
            "comment_crawl_count": comment_crawl_count,
        }
    except Exception as exc:
        db.rollback()
        # Why: 失败也要把任务行落到 failed,方便前端展示
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
