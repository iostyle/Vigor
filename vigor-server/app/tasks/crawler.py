import asyncio
from datetime import datetime

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.services.heat_calculator import calculate_heat_score
from app.services.platform_client import get_client
from app.tasks.processor import generate_summary_task


def _get_client_for_platform(platform: str | None):
    """按显式传入的 platform 参数选择具体平台 client,默认 'douyin'"""
    return get_client(platform or "douyin")


def _parse_time(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


@celery_app.task(
    name="app.tasks.crawler.crawl_keyword",
    queue="crawler",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def crawl_keyword_task(self, keyword_id: int, platform: str = "douyin"):
    """按关键词在指定平台爬取视频与热门评论,并派发摘要任务

    platform 从 trigger_crawl API 请求体传入,不再依赖 keyword.platform
    (keyword 和 platform 已正交,同一关键词可在多平台使用)
    """
    db = SessionLocal()
    task_record = CrawlTask(
        keyword_id=keyword_id,
        task_type="crawl",
        status="running",
        started_at=datetime.now(),
    )

    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword:
            return {"status": "error", "message": f"Keyword {keyword_id} not found"}

        if keyword.status != "active":
            return {"status": "skipped", "reason": "keyword disabled"}

        client = _get_client_for_platform(platform)

        raw_videos = asyncio.run(
            client.search_videos(
                keyword.keyword,
                time_window="30d",
                limit=100,
                min_heat=keyword.crawl_threshold or 1000,
            )
        )

        existing_ids = {
            v.external_id
            for v in db.query(Video)
            .filter(
                Video.platform == platform,
                Video.external_id.in_([r["external_id"] for r in raw_videos]),
            )
            .all()
        }

        saved_videos: list[Video] = []
        for item in raw_videos:
            if item["external_id"] in existing_ids:
                continue

            publish_time = _parse_time(item.get("publish_time"))
            heat = None
            if publish_time is not None:
                heat = calculate_heat_score(
                    item.get("like_count", 0),
                    item.get("comment_count", 0),
                    item.get("share_count", 0),
                    publish_time,
                )

            video = Video(
                platform=item.get("platform", platform),
                external_id=item["external_id"],
                keyword_id=keyword_id,
                title=item.get("title", ""),
                author_name=item.get("author_name"),
                author_id=item.get("author_id"),
                cover_url=item.get("cover_url"),
                video_url=item.get("video_url"),
                like_count=item.get("like_count", 0),
                comment_count=item.get("comment_count", 0),
                share_count=item.get("share_count", 0),
                publish_time=publish_time,
                heat_score=heat,
                last_updated_at=datetime.now(),
            )
            db.add(video)
            saved_videos.append(video)

        db.flush()

        for video in saved_videos:
            raw_comments = asyncio.run(
                client.get_comments(video.external_id, limit=50, sort_by="like")
            )
            for c in raw_comments:
                db.add(
                    Comment(
                        video_id=video.id,
                        platform=c.get("platform", platform),
                        external_comment_id=c.get("external_comment_id"),
                        author_name=c.get("author_name"),
                        content=c.get("content", ""),
                        like_count=c.get("like_count", 0),
                        publish_time=_parse_time(c.get("publish_time")),
                    )
                )

        task_record.videos_crawled = len(saved_videos)
        task_record.status = "success"
        task_record.completed_at = datetime.now()
        db.add(task_record)
        db.commit()

        for video in saved_videos:
            generate_summary_task.delay(video.id)

        return {
            "status": "success",
            "keyword_id": keyword_id,
            "videos_crawled": len(saved_videos),
        }

    except Exception as exc:
        db.rollback()
        task_record.status = "failed"
        task_record.error_message = str(exc)
        task_record.completed_at = datetime.now()
        try:
            db.add(task_record)
            db.commit()
        except Exception:
            db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.crawler.crawl_video_comments",
    queue="crawler",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def crawl_video_comments(self, video_id: int):
    """重新爬取指定视频的热门评论(由 updater 在评论增长 >20% 时触发)"""
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": f"Video {video_id} not found"}

        # Why: platform 直接从 video 取,video 上已经存了归属平台
        client = _get_client_for_platform(video.platform)
        raw_comments = asyncio.run(
            client.get_comments(video.external_id, limit=50, sort_by="like")
        )

        existing_ids = {
            c.external_comment_id
            for c in db.query(Comment).filter(Comment.video_id == video_id).all()
        }

        new_count = 0
        for c in raw_comments:
            cid = c.get("external_comment_id")
            if cid in existing_ids:
                continue
            db.add(
                Comment(
                    video_id=video_id,
                    platform=c.get("platform", video.platform),
                    external_comment_id=cid,
                    author_name=c.get("author_name"),
                    content=c.get("content", ""),
                    like_count=c.get("like_count", 0),
                    publish_time=_parse_time(c.get("publish_time")),
                )
            )
            new_count += 1

        db.commit()
        generate_summary_task.delay(video_id)
        return {"status": "success", "video_id": video_id, "new_comments": new_count}

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.crawler.crawl_all_keywords",
    queue="crawler",
)
def crawl_all_keywords():
    """定时派发所有 active 关键词的爬取任务(按 priority 降序)

    Phase 1 下默认按 'douyin' 派发。Phase 2 扩展时可按 keyword 关联的平台集合
    派发多任务,或由调度配置显式指定目标平台。
    """
    db = SessionLocal()
    try:
        keywords = (
            db.query(Keyword)
            .filter(Keyword.status == "active")
            .order_by(Keyword.priority.desc())
            .all()
        )
        for kw in keywords:
            crawl_keyword_task.delay(kw.id, "douyin")
        return {"status": "success", "dispatched": len(keywords)}
    finally:
        db.close()
