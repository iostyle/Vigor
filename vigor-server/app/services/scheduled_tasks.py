import json
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.keyword import Keyword
from app.models.scheduled_task import ScheduledTask
from app.models.scheduled_task_run import ScheduledTaskRun
from app.models.task import CrawlTask
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


def dispatch_scheduled_task(
    db: Session,
    task: ScheduledTask,
    source: str = "scheduled",
    source_id: int | None = None,
) -> list[int]:
    source_id = source_id if source_id is not None else task.id
    if task.task_kind == "crawl":
        if task.target_mode == "keyword":
            task_ids, _ = dispatch_crawl_keyword(
                db,
                task.target_id,
                task.platform or "bilibili",
                source=source,
                source_id=source_id,
            )
        elif task.target_mode == "category":
            task_ids, _, _ = dispatch_crawl_category(
                db,
                task.target_id,
                task.platform or "bilibili",
                source=source,
                source_id=source_id,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid crawl target",
            )
    elif task.task_kind == "update":
        if task.target_mode == "video":
            task_ids, _ = dispatch_update_video(
                db,
                task.target_id,
                source=source,
                source_id=source_id,
            )
        elif task.target_mode == "keyword":
            task_ids, _, _ = dispatch_update_keyword(
                db,
                task.target_id,
                task.limit or 20,
                source=source,
                source_id=source_id,
            )
        elif task.target_mode == "category":
            task_ids, _, _ = dispatch_update_category(
                db,
                task.target_id,
                task.limit or 100,
                source=source,
                source_id=source_id,
                platform=task.platform or "bilibili",
            )
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
    run = ScheduledTaskRun(
        status="running",
        started_at=current,
        due_count=0,
        dispatched_count=0,
        failed_count=0,
        triggered_task_ids=json.dumps([]),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    due_tasks = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.enabled.is_(True))
        .filter(ScheduledTask.next_run_at <= current)
        .all()
    )

    dispatched = 0
    failed = 0
    triggered_task_ids: list[int] = []
    errors: list[str] = []
    for task in due_tasks:
        try:
            task_ids = dispatch_scheduled_task(
                db,
                task,
                source="scheduled",
                source_id=task.id,
            )
            dispatched += 1
            triggered_task_ids.extend(task_ids)
            task.last_task_ids = json.dumps(task_ids)
            task.last_run_at = current
        except Exception as exc:
            failed += 1
            task.last_task_ids = json.dumps([])
            task.last_run_at = current
            errors.append(f"定时任务 {task.id}: {exc}")
            # Why: 调度器不能因为一个配置失败而阻塞后续配置继续运行。
            logger.warning("scheduled task %s failed: %s", task.id, exc)
        finally:
            task.next_run_at = compute_next_run(task, current)
            db.add(task)
            db.commit()

    run.due_count = len(due_tasks)
    run.dispatched_count = dispatched
    run.failed_count = failed
    run.triggered_task_ids = json.dumps(triggered_task_ids)
    run.status = "failed" if failed else "success"
    run.error_message = "\n".join(errors) if errors else None
    run.finished_at = now or datetime.now()
    db.add(run)
    db.commit()

    return dispatched


def parse_task_ids(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [int(item) for item in parsed if item is not None]


def get_scheduler_monitor(db: Session, now: datetime | None = None) -> dict:
    current = now or datetime.now()
    last_run = db.query(ScheduledTaskRun).order_by(ScheduledTaskRun.started_at.desc()).first()
    enabled_count = db.query(ScheduledTask).filter(ScheduledTask.enabled.is_(True)).count()
    disabled_count = db.query(ScheduledTask).filter(ScheduledTask.enabled.is_(False)).count()
    due_count = (
        db.query(ScheduledTask)
        .filter(ScheduledTask.enabled.is_(True))
        .filter(ScheduledTask.next_run_at <= current)
        .count()
    )

    health_status = "stalled"
    health_message = "调度器还没有扫描记录"
    seconds_since_last_run = None
    if last_run is not None:
        seconds_since_last_run = int((current - last_run.started_at).total_seconds())
        if seconds_since_last_run <= 120 and due_count == 0:
            health_status = "healthy"
            health_message = "调度器运行正常"
        elif seconds_since_last_run <= 300:
            health_status = "delayed"
            health_message = "存在待触发任务或调度器略有延迟"
        else:
            health_status = "stalled"
            health_message = "调度器超过 5 分钟没有扫描记录"

    since = current - timedelta(hours=24)
    scheduled_task_query = (
        db.query(CrawlTask)
        .filter(CrawlTask.source == "scheduled")
        .filter(CrawlTask.started_at >= since)
    )
    last_24h_total = scheduled_task_query.count()
    last_24h_success = scheduled_task_query.filter(CrawlTask.status == "success").count()
    last_24h_failed = scheduled_task_query.filter(CrawlTask.status == "failed").count()
    last_24h_running = scheduled_task_query.filter(CrawlTask.status.in_(["pending", "running"])).count()

    source_rows = (
        db.query(CrawlTask.source, func.count(CrawlTask.id))
        .group_by(CrawlTask.source)
        .all()
    )
    source_counts = {row[0] or "legacy": row[1] for row in source_rows}

    recent_tasks = (
        db.query(CrawlTask)
        .filter(CrawlTask.source == "scheduled")
        .order_by(CrawlTask.id.desc())
        .limit(10)
        .all()
    )
    recent_runs = (
        db.query(ScheduledTaskRun)
        .order_by(ScheduledTaskRun.started_at.desc())
        .limit(10)
        .all()
    )

    return {
        "server_time": current,
        "health": {
            "status": health_status,
            "message": health_message,
            "seconds_since_last_run": seconds_since_last_run,
        },
        "scheduler": {
            "last_run_at": last_run.started_at if last_run else None,
            "last_finished_at": last_run.finished_at if last_run else None,
            "last_status": last_run.status if last_run else None,
            "last_due_count": last_run.due_count if last_run else 0,
            "last_dispatched_count": last_run.dispatched_count if last_run else 0,
            "last_failed_count": last_run.failed_count if last_run else 0,
        },
        "tasks": {
            "enabled_count": enabled_count,
            "disabled_count": disabled_count,
            "due_count": due_count,
            "last_24h_total": last_24h_total,
            "last_24h_success": last_24h_success,
            "last_24h_failed": last_24h_failed,
            "last_24h_running": last_24h_running,
            "source_counts": source_counts,
        },
        "recent_tasks": [
            {
                "id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "source": task.source or "legacy",
                "source_id": task.source_id,
                "keyword_id": task.keyword_id,
                "videos_crawled": task.videos_crawled or 0,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
            }
            for task in recent_tasks
        ],
        "recent_runs": [
            {
                "id": run.id,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "due_count": run.due_count,
                "dispatched_count": run.dispatched_count,
                "failed_count": run.failed_count,
                "triggered_task_ids": parse_task_ids(run.triggered_task_ids),
                "error_message": run.error_message,
            }
            for run in recent_runs
        ],
    }


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
