import json
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.keyword import Keyword
from app.models.scheduled_task import ScheduledTask
from app.models.video import Video
from app.services.task_dispatcher import (
    dispatch_crawl_category,
    dispatch_crawl_keyword,
    dispatch_update_category,
    dispatch_update_keyword,
    dispatch_update_video,
)

logger = logging.getLogger(__name__)


def compute_next_run(task: ScheduledTask, now: datetime | None = None) -> datetime | None:
    if not task.enabled:
        return None

    base = (now or datetime.now()).replace(second=0, microsecond=0)
    if task.schedule_type == "interval":
        minutes = task.interval_minutes or 60
        return base + timedelta(minutes=minutes)

    if task.schedule_type == "daily" and task.daily_time:
        hour, minute = [int(part) for part in task.daily_time.split(":")]
        candidate = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= base:
            candidate += timedelta(days=1)
        return candidate

    return None


def validate_scheduled_task(task: ScheduledTask) -> None:
    if task.task_kind == "crawl" and task.target_mode == "video":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Crawl scheduled task does not support video target",
        )
    if task.target_mode in {"category", "keyword", "video"} and not task.target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_id is required",
        )
    if task.schedule_type == "interval" and not task.interval_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="interval_minutes is required",
        )
    if task.schedule_type == "daily" and not task.daily_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="daily_time is required",
        )
    if task.task_kind == "update" and task.target_mode != "video" and not task.limit:
        task.limit = 20 if task.target_mode == "keyword" else 100


def dispatch_scheduled_task(db: Session, task: ScheduledTask) -> list[int]:
    if task.task_kind == "crawl":
        if task.target_mode == "keyword":
            task_ids, _ = dispatch_crawl_keyword(
                db,
                task.target_id,
                task.platform or "bilibili",
            )
        elif task.target_mode == "category":
            task_ids, _, _ = dispatch_crawl_category(
                db,
                task.target_id,
                task.platform or "bilibili",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid crawl target",
            )
    elif task.task_kind == "update":
        if task.target_mode == "video":
            task_ids, _ = dispatch_update_video(db, task.target_id)
        elif task.target_mode == "keyword":
            task_ids, _, _ = dispatch_update_keyword(db, task.target_id, task.limit or 20)
        elif task.target_mode == "category":
            task_ids, _, _ = dispatch_update_category(db, task.target_id, task.limit or 100)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid update target",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scheduled task kind",
        )
    return task_ids


def run_due_scheduled_tasks(db: Session, now: datetime | None = None) -> int:
    current = now or datetime.now()
    due_tasks = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.enabled.is_(True))
        .filter(ScheduledTask.next_run_at <= current)
        .all()
    )

    dispatched = 0
    for task in due_tasks:
        try:
            task_ids = dispatch_scheduled_task(db, task)
            dispatched += 1
            task.last_task_ids = json.dumps(task_ids)
            task.last_run_at = current
        except Exception as exc:
            task.last_task_ids = json.dumps([])
            task.last_run_at = current
            # Why: 调度器不能因为一个配置失败而阻塞后续配置继续运行。
            logger.warning("scheduled task %s failed: %s", task.id, exc)
        finally:
            task.next_run_at = compute_next_run(task, current)
            db.add(task)
            db.commit()

    return dispatched


def get_target_label(db: Session, task: ScheduledTask) -> str | None:
    if task.target_mode == "category" and task.target_id:
        row = db.query(Category.name).filter(Category.id == task.target_id).first()
        return row.name if row else None
    if task.target_mode == "keyword" and task.target_id:
        row = db.query(Keyword.keyword).filter(Keyword.id == task.target_id).first()
        return row.keyword if row else None
    if task.target_mode == "video" and task.target_id:
        row = db.query(Video.title).filter(Video.id == task.target_id).first()
        return row.title if row else None
    return None
