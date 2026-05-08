from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.schemas.task import CrawlTaskResponse
from app.tasks.crawler import crawl_keyword_task

router = APIRouter(
    prefix="/api/admin/tasks",
    tags=["admin-tasks"],
    dependencies=[Depends(verify_api_key)],
)


class CrawlTriggerRequest(BaseModel):
    keyword_id: int


class UpdateTriggerRequest(BaseModel):
    video_id: Optional[int] = None
    keyword_id: Optional[int] = None


class TaskTriggerResponse(BaseModel):
    task_id: int
    celery_task_id: str
    status: str


def _enqueue_celery_task(task_name: str, *args) -> str:
    # Why: 之前是占位字符串,worker 永远不会真跑;现在按 task_name 派发到对应 Celery task。
    # update_videos 暂未实现,仍返回占位
    if task_name == "crawl_keyword":
        result = crawl_keyword_task.delay(*args)
        return result.id
    return f"celery-{task_name}-placeholder"


@router.post(
    "/crawl",
    response_model=TaskTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_crawl(
    payload: CrawlTriggerRequest,
    db: Session = Depends(get_db),
) -> TaskTriggerResponse:
    keyword = db.query(Keyword).filter(Keyword.id == payload.keyword_id).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found",
        )

    task = CrawlTask(
        keyword_id=payload.keyword_id,
        task_type="crawl",
        status="pending",
        videos_crawled=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task_id = _enqueue_celery_task("crawl_keyword", payload.keyword_id)

    return TaskTriggerResponse(
        task_id=task.id,
        celery_task_id=celery_task_id,
        status=task.status,
    )


@router.post(
    "/update",
    response_model=TaskTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_update(
    payload: UpdateTriggerRequest,
    db: Session = Depends(get_db),
) -> TaskTriggerResponse:
    if payload.video_id is None and payload.keyword_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either video_id or keyword_id must be provided",
        )

    if payload.video_id is not None:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

    if payload.keyword_id is not None:
        keyword = db.query(Keyword).filter(Keyword.id == payload.keyword_id).first()
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keyword not found",
            )

    task = CrawlTask(
        keyword_id=payload.keyword_id,
        task_type="update",
        status="pending",
        videos_crawled=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task_id = _enqueue_celery_task(
        "update_videos", payload.video_id, payload.keyword_id, task.id
    )

    return TaskTriggerResponse(
        task_id=task.id,
        celery_task_id=celery_task_id,
        status=task.status,
    )


@router.get("", response_model=list[CrawlTaskResponse])
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CrawlTaskResponse]:
    offset = (page - 1) * page_size
    tasks = (
        db.query(CrawlTask)
        .order_by(CrawlTask.started_at.desc().nullslast())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [CrawlTaskResponse.model_validate(t) for t in tasks]
