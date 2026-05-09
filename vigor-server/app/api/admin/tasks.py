from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.category import Category
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.schemas.task import CrawlTaskResponse
from app.tasks.crawler import crawl_keyword_task
from app.tasks.updater import update_selection_task

router = APIRouter(
    prefix="/api/admin/tasks",
    tags=["admin-tasks"],
    dependencies=[Depends(verify_api_key)],
)


class CrawlTriggerRequest(BaseModel):
    keyword_id: int
    platform: str = "douyin"


class CrawlByCategoryRequest(BaseModel):
    category_id: int
    platform: str = "douyin"


class CrawlByCategoryResponse(BaseModel):
    category_id: int
    keyword_count: int
    task_ids: list[int]
    celery_task_ids: list[str]
    status: str


class UpdateTriggerRequest(BaseModel):
    video_id: Optional[int] = None
    keyword_id: Optional[int] = None


class TaskTriggerResponse(BaseModel):
    task_id: int
    celery_task_id: str
    status: str


def _enqueue_celery_task(task_name: str, *args) -> str:
    # Why: 之前是占位字符串,worker 永远不会真跑;现在按 task_name 派发到对应 Celery task。
    if task_name == "crawl_keyword":
        result = crawl_keyword_task.delay(*args)
        return result.id
    if task_name == "update_videos":
        # args = (video_id, keyword_id, task_id)
        result = update_selection_task.delay(*args)
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
        started_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    celery_task_id = _enqueue_celery_task("crawl_keyword", payload.keyword_id, payload.platform, task.id)

    return TaskTriggerResponse(
        task_id=task.id,
        celery_task_id=celery_task_id,
        status=task.status,
    )


@router.post(
    "/crawl-by-category",
    response_model=CrawlByCategoryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_crawl_by_category(
    payload: CrawlByCategoryRequest,
    db: Session = Depends(get_db),
) -> CrawlByCategoryResponse:
    """按领域批量触发爬取:对该领域下所有 active 关键词,各创建一个
    CrawlTask 行并 .delay() 派发 crawl_keyword_task。"""
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    keywords = (
        db.query(Keyword)
        .filter(
            Keyword.category_id == payload.category_id,
            Keyword.status == "active",
        )
        .all()
    )
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active keywords in this category",
        )

    # Why: 先把所有 task 行落库取到 id,再统一派 celery,避免出现
    # "celery 收到任务但 DB 还没那行"的竞态
    tasks: list[CrawlTask] = []
    for kw in keywords:
        t = CrawlTask(
            keyword_id=kw.id,
            task_type="crawl",
            status="pending",
            videos_crawled=0,
            started_at=datetime.utcnow(),
        )
        db.add(t)
        tasks.append(t)
    db.commit()
    for t in tasks:
        db.refresh(t)

    task_ids: list[int] = []
    celery_task_ids: list[str] = []
    for kw, t in zip(keywords, tasks):
        cid = _enqueue_celery_task("crawl_keyword", kw.id, payload.platform, t.id)
        task_ids.append(t.id)
        celery_task_ids.append(cid)

    return CrawlByCategoryResponse(
        category_id=payload.category_id,
        keyword_count=len(keywords),
        task_ids=task_ids,
        celery_task_ids=celery_task_ids,
        status="pending",
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
        started_at=datetime.utcnow(),
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
        .order_by(CrawlTask.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [CrawlTaskResponse.model_validate(t) for t in tasks]
