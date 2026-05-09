from datetime import datetime
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
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
    # Why: 按 keyword 更新会越积越多视频,默认 20 条避免一次刷一两百条
    # 把 worker 占满。video_id 模式忽略此参数(单条不需要)。
    limit: int = Field(default=20, ge=1, le=500)


class UpdateByCategoryRequest(BaseModel):
    category_id: int
    limit: int = Field(default=100, ge=1, le=1000)


class BatchUpdateTriggerResponse(BaseModel):
    """按 keyword / category 批量更新的响应:每个 video 一条 task 行。"""
    keyword_id: Optional[int] = None
    category_id: Optional[int] = None
    video_count: int
    limit: int
    task_ids: list[int]
    celery_task_ids: list[str]
    status: str


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


def _bulk_dispatch_video_updates(
    db: Session, videos: list[Video]
) -> tuple[list[int], list[str]]:
    """为每条 video 创建一行 CrawlTask(task_type='update'),并 .delay()
    update_selection_task。先全部落库再统一派任务,避免 worker 抢先。

    返回 (task_ids, celery_task_ids)。
    """
    task_rows: list[CrawlTask] = []
    for v in videos:
        t = CrawlTask(
            keyword_id=v.keyword_id,
            video_id=v.id,
            task_type="update",
            status="pending",
            videos_crawled=0,
            started_at=datetime.utcnow(),
        )
        db.add(t)
        task_rows.append(t)
    db.commit()
    for t in task_rows:
        db.refresh(t)

    task_ids: list[int] = []
    celery_task_ids: list[str] = []
    for v, t in zip(videos, task_rows):
        cid = _enqueue_celery_task("update_videos", v.id, None, t.id)
        task_ids.append(t.id)
        celery_task_ids.append(cid)
    return task_ids, celery_task_ids


@router.post(
    "/update",
    response_model=Union[TaskTriggerResponse, BatchUpdateTriggerResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_update(
    payload: UpdateTriggerRequest,
    db: Session = Depends(get_db),
):
    """触发数据更新。

    - video_id 模式:单条 task,行为不变,响应仍是 TaskTriggerResponse
    - keyword_id 模式:取该关键词下 publish_time 降序的最新 limit 条视频,
      每条 video 一行 task + 一次 .delay,响应为 BatchUpdateTriggerResponse
    """
    if payload.video_id is None and payload.keyword_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either video_id or keyword_id must be provided",
        )

    # ---- 单视频模式:保持既有 TaskTriggerResponse 形状 ----
    if payload.video_id is not None:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
            )
        task = CrawlTask(
            keyword_id=video.keyword_id,
            video_id=video.id,
            task_type="update",
            status="pending",
            videos_crawled=0,
            started_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        celery_task_id = _enqueue_celery_task(
            "update_videos", payload.video_id, None, task.id
        )
        return TaskTriggerResponse(
            task_id=task.id,
            celery_task_id=celery_task_id,
            status=task.status,
        )

    # ---- 关键词模式:批量,每条 video 一行 task,limit 截断 ----
    keyword = db.query(Keyword).filter(Keyword.id == payload.keyword_id).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found"
        )
    videos = (
        db.query(Video)
        .filter(Video.keyword_id == payload.keyword_id)
        .order_by(Video.publish_time.desc().nullslast(), Video.id.desc())
        .limit(payload.limit)
        .all()
    )
    if not videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No videos found for this keyword",
        )

    task_ids, celery_task_ids = _bulk_dispatch_video_updates(db, videos)
    return BatchUpdateTriggerResponse(
        keyword_id=payload.keyword_id,
        video_count=len(videos),
        limit=payload.limit,
        task_ids=task_ids,
        celery_task_ids=celery_task_ids,
        status="pending",
    )


@router.post(
    "/update-by-category",
    response_model=BatchUpdateTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_update_by_category(
    payload: UpdateByCategoryRequest,
    db: Session = Depends(get_db),
) -> BatchUpdateTriggerResponse:
    """按领域批量更新:取该领域下所有 active keyword 的 publish_time
    降序最新 limit 条视频,每条一行 task + 一次 .delay。"""
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    keyword_ids = [
        row.id
        for row in db.query(Keyword.id)
        .filter(
            Keyword.category_id == payload.category_id,
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
        .limit(payload.limit)
        .all()
    )
    if not videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No videos found in this category",
        )

    task_ids, celery_task_ids = _bulk_dispatch_video_updates(db, videos)
    return BatchUpdateTriggerResponse(
        category_id=payload.category_id,
        video_count=len(videos),
        limit=payload.limit,
        task_ids=task_ids,
        celery_task_ids=celery_task_ids,
        status="pending",
    )


class CrawlTaskListResponse(BaseModel):
    """任务历史分页响应:total 给前端正确分页,data 是当前页。"""
    total: int
    data: list[CrawlTaskResponse]


def _build_task_summaries(
    db: Session, tasks: list[CrawlTask]
) -> dict[int, str]:
    """批量为一页 task 生成摘要文本,避免 N+1。

    策略:
    - 批量查 keyword_id → keyword.keyword 映射
    - 批量查每个 keyword_id 下最新一条 video 的 title(用于 crawl 摘要)
    - 批量查 video_id → video.title 映射(用于 update 摘要)
    - 按 task_type + videos_crawled 拼文案
    """
    if not tasks:
        return {}

    keyword_ids = list({t.keyword_id for t in tasks if t.keyword_id})

    # 批量加载关键词名
    kw_map: dict[int, str] = {}
    if keyword_ids:
        rows = db.query(Keyword.id, Keyword.keyword).filter(Keyword.id.in_(keyword_ids)).all()
        kw_map = {r.id: r.keyword for r in rows}

    # 批量加载每个 keyword_id 下最新一条 video title(用于 crawl 类型)
    first_video_map: dict[int, str] = {}
    for kid in keyword_ids:
        v = (
            db.query(Video.title)
            .filter(Video.keyword_id == kid)
            .order_by(Video.id.desc())
            .limit(1)
            .first()
        )
        if v:
            first_video_map[kid] = v.title or ""

    # 批量加载 video_id → title(用于 update 类型精确显示)
    video_ids = list({t.video_id for t in tasks if t.video_id})
    video_title_map: dict[int, str] = {}
    if video_ids:
        rows = db.query(Video.id, Video.title).filter(Video.id.in_(video_ids)).all()
        video_title_map = {r.id: (r.title or "") for r in rows}

    summaries: dict[int, str] = {}
    for t in tasks:
        kw_name = kw_map.get(t.keyword_id, "")
        count = t.videos_crawled or 0

        if t.task_type == "crawl":
            video_title = first_video_map.get(t.keyword_id, "")
            short_title = video_title[:20] if video_title else ""
            if count > 0 and short_title:
                summaries[t.id] = f"爬取了「{short_title}」等 {count} 个视频"
            elif count > 0:
                summaries[t.id] = f"爬取关键词「{kw_name}」,共 {count} 个视频"
            else:
                summaries[t.id] = f"爬取关键词「{kw_name}」"
        elif t.task_type == "update":
            # 优先用 video_id 查精确标题
            if t.video_id and t.video_id in video_title_map:
                title = video_title_map[t.video_id][:20]
                if title:
                    summaries[t.id] = f"更新了「{title}」"
                else:
                    summaries[t.id] = f"更新了关键词「{kw_name}」下 1 个视频"
            elif count == 1:
                summaries[t.id] = f"更新了关键词「{kw_name}」下 1 个视频"
            elif count > 1:
                summaries[t.id] = f"更新了关键词「{kw_name}」下 {count} 个视频"
            else:
                summaries[t.id] = f"更新关键词「{kw_name}」"
        else:
            summaries[t.id] = t.task_type

    return summaries


@router.get("", response_model=CrawlTaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> CrawlTaskListResponse:
    total = db.query(CrawlTask).count()
    offset = (page - 1) * page_size
    tasks = (
        db.query(CrawlTask)
        .order_by(CrawlTask.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    summaries = _build_task_summaries(db, tasks)

    data: list[CrawlTaskResponse] = []
    for t in tasks:
        resp = CrawlTaskResponse.model_validate(t)
        resp.summary = summaries.get(t.id)
        data.append(resp)

    return CrawlTaskListResponse(total=total, data=data)
