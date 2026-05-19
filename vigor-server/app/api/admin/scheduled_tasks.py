import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.scheduled_task import ScheduledTask
from app.schemas.scheduled_task import (
    ScheduledTaskCreate,
    ScheduledTaskListResponse,
    ScheduledTaskResponse,
    ScheduledTaskToggle,
    ScheduledTaskUpdate,
)
from app.services.scheduled_tasks import compute_next_run, get_target_label, validate_scheduled_task

router = APIRouter(
    prefix="/api/admin/scheduled-tasks",
    tags=["admin-scheduled-tasks"],
    dependencies=[Depends(verify_api_key)],
)


def _to_response(db: Session, task: ScheduledTask) -> ScheduledTaskResponse:
    last_task_ids: list[int] = []
    if task.last_task_ids:
        try:
            parsed = json.loads(task.last_task_ids)
            if isinstance(parsed, list):
                last_task_ids = [int(item) for item in parsed]
        except (TypeError, ValueError):
            last_task_ids = []

    return ScheduledTaskResponse.model_validate(
        {
            "id": task.id,
            "name": task.name,
            "task_kind": task.task_kind,
            "target_mode": task.target_mode,
            "target_id": task.target_id,
            "platform": task.platform,
            "limit": task.limit,
            "schedule_type": task.schedule_type,
            "interval_minutes": task.interval_minutes,
            "daily_time": task.daily_time,
            "enabled": task.enabled,
            "last_run_at": task.last_run_at,
            "next_run_at": task.next_run_at,
            "last_task_ids": last_task_ids,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "target_label": get_target_label(db, task),
        }
    )


@router.get("", response_model=ScheduledTaskListResponse)
def list_scheduled_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScheduledTaskListResponse:
    query = db.query(ScheduledTask)
    total = query.count()
    tasks = (
        query.order_by(ScheduledTask.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ScheduledTaskListResponse(total=total, data=[_to_response(db, task) for task in tasks])


@router.post("", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_task(
    payload: ScheduledTaskCreate,
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    task = ScheduledTask(**payload.model_dump())
    validate_scheduled_task(task)
    task.next_run_at = compute_next_run(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_response(db, task)


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
def update_scheduled_task(
    task_id: int,
    payload: ScheduledTaskUpdate,
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled task not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    validate_scheduled_task(task)
    task.updated_at = datetime.utcnow()
    task.next_run_at = compute_next_run(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_response(db, task)


@router.patch("/{task_id}/enabled", response_model=ScheduledTaskResponse)
def toggle_scheduled_task(
    task_id: int,
    payload: ScheduledTaskToggle,
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled task not found")

    task.enabled = payload.enabled
    task.updated_at = datetime.utcnow()
    task.next_run_at = compute_next_run(task)
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_response(db, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> None:
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled task not found")
    db.delete(task)
    db.commit()
