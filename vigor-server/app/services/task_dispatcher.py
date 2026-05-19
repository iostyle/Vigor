import json
from datetime import datetime
from typing import Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.tasks.crawler import crawl_keyword_task
from app.tasks.updater import update_selection_task


def enqueue_celery_task(task_name: str, *args) -> str:
    if task_name == "crawl_keyword":
        result = crawl_keyword_task.delay(*args)
        return result.id
    if task_name == "update_videos":
        result = update_selection_task.delay(*args)
        return result.id
    return f"celery-{task_name}-placeholder"


def get_active_keyword_or_404(db: Session, keyword_id: int) -> Keyword:
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found",
        )
    if keyword.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keyword is not active",
        )
    return keyword


def dispatch_crawl_keyword(
    db: Session,
    keyword_id: int,
    platform: str,
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str]]:
    get_active_keyword_or_404(db, keyword_id)

    task = CrawlTask(
        keyword_id=keyword_id,
        task_type="crawl",
        source=source,
        source_id=source_id,
        status="pending",
        videos_crawled=0,
        started_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task_id = enqueue("crawl_keyword", keyword_id, platform, task.id)
    return [task.id], [celery_task_id]


def dispatch_crawl_category(
    db: Session,
    category_id: int,
    platform: str,
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str], int]:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    keywords = (
        db.query(Keyword)
        .filter(
            Keyword.category_id == category_id,
            Keyword.status == "active",
        )
        .all()
    )
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active keywords in this category",
        )

    tasks: list[CrawlTask] = []
    for kw in keywords:
        task = CrawlTask(
            keyword_id=kw.id,
            task_type="crawl",
            source=source,
            source_id=source_id,
            status="pending",
            videos_crawled=0,
            started_at=datetime.utcnow(),
        )
        db.add(task)
        tasks.append(task)
    db.commit()
    for task in tasks:
        db.refresh(task)

    task_ids: list[int] = []
    celery_task_ids: list[str] = []
    for keyword, task in zip(keywords, tasks):
        celery_task_id = enqueue("crawl_keyword", keyword.id, platform, task.id)
        task_ids.append(task.id)
        celery_task_ids.append(celery_task_id)
    return task_ids, celery_task_ids, len(keywords)


def dispatch_update_video(
    db: Session,
    video_id: int,
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str]]:
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found",
        )
    task_ids, celery_task_ids = dispatch_update_videos(
        db, [video], enqueue, source, source_id
    )
    return task_ids, celery_task_ids


def dispatch_update_keyword(
    db: Session,
    keyword_id: int,
    limit: int,
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str], int]:
    get_active_keyword_or_404(db, keyword_id)
    videos = (
        db.query(Video)
        .filter(Video.keyword_id == keyword_id)
        .order_by(Video.publish_time.desc().nullslast(), Video.id.desc())
        .limit(limit)
        .all()
    )
    if not videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No videos found for this keyword",
        )

    task_ids, celery_task_ids = dispatch_update_videos(
        db, videos, enqueue, source, source_id
    )
    return task_ids, celery_task_ids, len(videos)


def dispatch_update_category(
    db: Session,
    category_id: int,
    limit: int,
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str], int]:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    keyword_ids = [
        row.id
        for row in db.query(Keyword.id)
        .filter(
            Keyword.category_id == category_id,
            Keyword.status == "active",
        )
        .all()
    ]
    if not keyword_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active keywords in this category",
        )

    videos = (
        db.query(Video)
        .filter(Video.keyword_id.in_(keyword_ids))
        .order_by(Video.publish_time.desc().nullslast(), Video.id.desc())
        .limit(limit)
        .all()
    )
    if not videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No videos found in this category",
        )

    task_ids, celery_task_ids = dispatch_update_videos(
        db, videos, enqueue, source, source_id
    )
    return task_ids, celery_task_ids, len(videos)


def dispatch_update_videos(
    db: Session,
    videos: list[Video],
    enqueue: Callable[..., str] = enqueue_celery_task,
    source: str = "manual",
    source_id: int | None = None,
) -> tuple[list[int], list[str]]:
    task_rows: list[CrawlTask] = []
    for video in videos:
        task = CrawlTask(
            keyword_id=video.keyword_id,
            video_ids=json.dumps([video.id]),
            task_type="update",
            source=source,
            source_id=source_id,
            status="pending",
            videos_crawled=0,
            started_at=datetime.utcnow(),
        )
        db.add(task)
        task_rows.append(task)
    db.commit()
    for task in task_rows:
        db.refresh(task)

    task_ids: list[int] = []
    celery_task_ids: list[str] = []
    for video, task in zip(videos, task_rows):
        celery_task_id = enqueue("update_videos", video.id, None, task.id)
        task_ids.append(task.id)
        celery_task_ids.append(celery_task_id)
    return task_ids, celery_task_ids
