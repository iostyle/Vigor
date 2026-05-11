import asyncio
import contextlib
import fcntl
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models.comment import Comment
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.services.heat_calculator import calculate_heat_score
from app.services.platform_client import get_client
from app.tasks.processor import generate_summary_task

logger = logging.getLogger(__name__)


def _enqueue_summary_if_enabled(video_id: int) -> None:
    if settings.AUTO_GENERATE_SUMMARY_AFTER_CRAWL:
        generate_summary_task.delay(video_id)

# MediaCrawler browser_data 目录,用于清理锁文件
_MC_ROOT = Path(__file__).resolve().parents[2] / "vendor_MediaCrawler"
_BROWSER_DATA_DIRS = {
    "bili": _MC_ROOT / "browser_data" / "bili_user_data_dir",
    "bilibili": _MC_ROOT / "browser_data" / "bili_user_data_dir",
    "dy": _MC_ROOT / "browser_data" / "dy_user_data_dir",
    "douyin": _MC_ROOT / "browser_data" / "dy_user_data_dir",
}
_LOCK_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")


def _normalize_platform(platform: str | None) -> str:
    return (platform or "douyin").lower()


def _browser_data_dir_for(platform: str | None) -> Path | None:
    return _BROWSER_DATA_DIRS.get(_normalize_platform(platform))


def _client_manages_browser_profile(platform: str | None) -> bool:
    return _normalize_platform(platform) in {"bili", "bilibili"}


@contextlib.contextmanager
def browser_profile_lock(platform: str | None):
    """串行化同一平台的持久化浏览器 profile 使用。"""
    user_data_dir = _browser_data_dir_for(platform)
    if not user_data_dir:
        yield
        return

    user_data_dir.parent.mkdir(parents=True, exist_ok=True)
    lock_path = user_data_dir.parent / f".{user_data_dir.name}.vigor.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def task_browser_profile_guard(platform: str | None):
    """保护仍由任务层管理的 MediaCrawler 浏览器 profile。"""
    if _client_manages_browser_profile(platform):
        yield
        return

    with browser_profile_lock(platform):
        cleanup_browser_locks(platform)
        try:
            yield
        finally:
            cleanup_browser_locks(platform)


def cleanup_browser_locks(platform: str) -> None:
    """清理指定平台的浏览器僵尸进程和锁文件。

    在爬取任务开始前和 finally 里调用,确保:
    1. 上次异常退出留下的锁不会阻塞本次
    2. 本次结束后不留残余给下次

    清理失败不抛异常,只 WARN 日志。
    """
    user_data_dir = _browser_data_dir_for(platform)
    if not user_data_dir:
        return

    dir_name = user_data_dir.name  # e.g. "bili_user_data_dir"

    # 1. 杀掉引用该 user_data_dir 的 chromium 进程
    try:
        subprocess.run(
            ["pkill", "-f", dir_name],
            timeout=5,
            capture_output=True,
        )
    except Exception as exc:
        logger.warning("cleanup_browser_locks pkill 失败 (%s): %s", dir_name, exc)

    # 2. 删除锁文件(可能是普通文件或 symlink)
    for name in _LOCK_FILES:
        lock_path = user_data_dir / name
        try:
            if lock_path.exists() or lock_path.is_symlink():
                lock_path.unlink()
                logger.info("已删除锁文件: %s", lock_path)
        except Exception as exc:
            logger.warning("删除锁文件失败 %s: %s", lock_path, exc)


def _get_client_for_platform(platform: str | None):
    """按显式传入的 platform 参数选择具体平台 client,默认 'douyin'"""
    return get_client(_normalize_platform(platform))


def _parse_time(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _clean_text(value, default: str | None = None) -> str | None:
    if value is None:
        return default
    return str(value).replace("\x00", "")


def _clean_tags(tags) -> str:
    return json.dumps([_clean_text(tag, "") for tag in (tags or [])], ensure_ascii=False)


def _mark_task_running(db, task_record: CrawlTask) -> None:
    db.add(task_record)
    db.commit()


def _dedupe_raw_videos(raw_videos: list[dict], platform: str) -> list[dict]:
    """按最终入库唯一键去掉本批重复视频。"""
    seen: set[tuple[str, str]] = set()
    deduped: list[dict] = []
    for item in raw_videos:
        external_id = _clean_text(item.get("external_id"), "")
        if not external_id:
            continue
        key = (_clean_text(item.get("platform") or platform, platform) or platform, external_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


@celery_app.task(
    name="app.tasks.crawler.crawl_keyword",
    queue="crawler",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def crawl_keyword_task(self, keyword_id: int, platform: str = "douyin", task_id: int | None = None):
    """按关键词在指定平台爬取视频与热门评论,并派发摘要任务

    platform 从 trigger_crawl API 请求体传入,不再依赖 keyword.platform
    (keyword 和 platform 已正交,同一关键词可在多平台使用)

    task_id: 由 trigger_crawl API 预创建的任务行 ID。传入则复用该行,
    不再另起 pending 行,避免出现"同一爬取在列表中有两条记录"。
    """
    db = SessionLocal()
    if task_id is not None:
        task_record = db.query(CrawlTask).filter(CrawlTask.id == task_id).first()
        if task_record is None:
            task_record = CrawlTask(
                keyword_id=keyword_id,
                task_type="crawl",
                status="running",
                started_at=datetime.utcnow(),
            )
        else:
            task_record.status = "running"
            task_record.started_at = datetime.utcnow()
    else:
        task_record = CrawlTask(
            keyword_id=keyword_id,
            task_type="crawl",
            status="running",
            started_at=datetime.utcnow(),
        )
    _mark_task_running(db, task_record)

    try:
        # Why: MediaCrawler 的持久化 Chromium profile 同平台不能并发使用。
        with task_browser_profile_guard(platform):
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
            raw_videos = _dedupe_raw_videos(raw_videos, platform)

            existing_ids = {
                v.external_id
                for v in db.query(Video)
                .filter(
                    Video.platform == platform,
                    Video.external_id.in_(
                        [_clean_text(r["external_id"], "") for r in raw_videos]
                    ),
                )
                .all()
            }

            saved_videos: list[Video] = []
            for item in raw_videos:
                external_id = _clean_text(item["external_id"], "")
                if external_id in existing_ids:
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
                    platform=_clean_text(item.get("platform", platform), platform),
                    external_id=external_id,
                    keyword_id=keyword_id,
                    title=_clean_text(item.get("title"), ""),
                    author_name=_clean_text(item.get("author_name")),
                    author_id=_clean_text(item.get("author_id")),
                    cover_url=_clean_text(item.get("cover_url")),
                    video_url=_clean_text(item.get("video_url")),
                    like_count=item.get("like_count", 0),
                    comment_count=item.get("comment_count", 0),
                    share_count=item.get("share_count", 0),
                    publish_time=publish_time,
                    heat_score=heat,
                    last_updated_at=datetime.utcnow(),
                    tags=_clean_tags(item.get("tags")),
                )
                db.add(video)
                saved_videos.append(video)

            db.flush()

            for video in saved_videos:
                try:
                    raw_comments = asyncio.run(
                        client.get_comments(video.external_id, limit=50, sort_by="like")
                    )
                except Exception as exc:
                    logger.warning(
                        "跳过视频评论爬取失败 video_id=%s platform=%s: %s",
                        video.external_id,
                        platform,
                        exc,
                    )
                    continue
                for c in raw_comments:
                    db.add(
                        Comment(
                            video_id=video.id,
                            platform=_clean_text(c.get("platform", platform), platform),
                            external_comment_id=_clean_text(c.get("external_comment_id")),
                            author_name=_clean_text(c.get("author_name")),
                            content=_clean_text(c.get("content"), ""),
                            like_count=c.get("like_count", 0),
                            publish_time=_parse_time(c.get("publish_time")),
                        )
                    )

        task_record.videos_crawled = len(saved_videos)
        task_record.video_ids = json.dumps([v.id for v in saved_videos])
        task_record.status = "success"
        task_record.error_message = None
        task_record.completed_at = datetime.utcnow()
        db.add(task_record)
        db.commit()

        for video in saved_videos:
            _enqueue_summary_if_enabled(video.id)

        return {
            "status": "success",
            "keyword_id": keyword_id,
            "videos_crawled": len(saved_videos),
        }

    except Exception as exc:
        db.rollback()
        task_record.status = "failed"
        task_record.error_message = str(exc)
        task_record.completed_at = datetime.utcnow()
        try:
            db.add(task_record)
            db.commit()
        except Exception:
            db.rollback()
        raise self.retry(exc=exc)
    finally:
        if not _client_manages_browser_profile(platform):
            with browser_profile_lock(platform):
                cleanup_browser_locks(platform)
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
    platform = "douyin"
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"status": "error", "message": f"Video {video_id} not found"}

        platform = video.platform or "douyin"
        with task_browser_profile_guard(platform):
            # Why: platform 直接从 video 取,video 上已经存了归属平台
            client = _get_client_for_platform(platform)
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
                    platform=_clean_text(c.get("platform", video.platform), video.platform),
                    external_comment_id=_clean_text(cid),
                    author_name=_clean_text(c.get("author_name")),
                    content=_clean_text(c.get("content"), ""),
                    like_count=c.get("like_count", 0),
                    publish_time=_parse_time(c.get("publish_time")),
                )
            )
            new_count += 1

        db.commit()
        _enqueue_summary_if_enabled(video_id)
        return {"status": "success", "video_id": video_id, "new_comments": new_count}

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        cleanup_browser_locks(platform)
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
