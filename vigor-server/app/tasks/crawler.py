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


def _get_client_for_keyword(keyword: Keyword):
    """按 keyword.platform 选择具体平台 client,默认 'douyin' 保持向后兼容"""
    return get_client(getattr(keyword, "platform", None) or "douyin")


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
def crawl_keyword_task(self, keyword_id: int):
    """按关键词爬取抖音视频与热门评论,并派发摘要任务"""
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

        client = _get_client_for_keyword(keyword)

        raw_videos = asyncio.run(
            client.search_videos(
                keyword.keyword,
                time_window="30d",
                limit=100,
                min_heat=keyword.crawl_threshold or 1000,
            )
        )

        existing_ids = {
            v.douyin_id
            for v in db.query(Video)
            .filter(Video.douyin_id.in_([r["douyin_id"] for r in raw_videos]))
            .all()
        }

        saved_videos: list[Video] = []
        for item in raw_videos:
            if item["douyin_id"] in existing_ids:
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
                douyin_id=item["douyin_id"],
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
                client.get_comments(video.douyin_id, limit=50, sort_by="like")
            )
            for c in raw_comments:
                db.add(
                    Comment(
                        video_id=video.id,
                        douyin_comment_id=c.get("douyin_comment_id"),
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

        # Why: 通过 video.keyword 路由到对应平台 client,而不是硬编码 douyin
        keyword = (
            db.query(Keyword).filter(Keyword.id == video.keyword_id).first()
            if video.keyword_id
            else None
        )
        if keyword is not None:
            client = _get_client_for_keyword(keyword)
        else:
            client = get_client("douyin")
        raw_comments = asyncio.run(
            client.get_comments(video.douyin_id, limit=50, sort_by="like")
        )

        existing_ids = {
            c.douyin_comment_id
            for c in db.query(Comment).filter(Comment.video_id == video_id).all()
        }

        new_count = 0
        for c in raw_comments:
            cid = c.get("douyin_comment_id")
            if cid in existing_ids:
                continue
            db.add(
                Comment(
                    video_id=video_id,
                    douyin_comment_id=cid,
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
    """定时派发所有 active 关键词的爬取任务(按 priority 降序)"""
    db = SessionLocal()
    try:
        keywords = (
            db.query(Keyword)
            .filter(Keyword.status == "active")
            .order_by(Keyword.priority.desc())
            .all()
        )
        for kw in keywords:
            crawl_keyword_task.delay(kw.id)
        return {"status": "success", "dispatched": len(keywords)}
    finally:
        db.close()
