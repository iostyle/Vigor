import json
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.schemas.task import CrawlTaskResponse
from app.services.task_dispatcher import (
    dispatch_crawl_category,
    dispatch_crawl_keyword,
    dispatch_update_category,
    dispatch_update_keyword,
    dispatch_update_video,
    enqueue_celery_task,
)

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
    return enqueue_celery_task(task_name, *args)


@router.post(
    "/crawl",
    response_model=TaskTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_crawl(
    payload: CrawlTriggerRequest,
    db: Session = Depends(get_db),
) -> TaskTriggerResponse:
    task_ids, celery_task_ids = dispatch_crawl_keyword(
        db, payload.keyword_id, payload.platform, _enqueue_celery_task
    )
    return TaskTriggerResponse(
        task_id=task_ids[0],
        celery_task_id=celery_task_ids[0],
        status="pending",
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
    task_ids, celery_task_ids, keyword_count = dispatch_crawl_category(
        db, payload.category_id, payload.platform, _enqueue_celery_task
    )

    return CrawlByCategoryResponse(
        category_id=payload.category_id,
        keyword_count=keyword_count,
        task_ids=task_ids,
        celery_task_ids=celery_task_ids,
        status="pending",
    )


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
        task_ids, celery_task_ids = dispatch_update_video(
            db, payload.video_id, _enqueue_celery_task
        )
        return TaskTriggerResponse(
            task_id=task_ids[0],
            celery_task_id=celery_task_ids[0],
            status="pending",
        )

    # ---- 关键词模式:批量,每条 video 一行 task,limit 截断 ----
    task_ids, celery_task_ids, video_count = dispatch_update_keyword(
        db, payload.keyword_id, payload.limit, _enqueue_celery_task
    )
    return BatchUpdateTriggerResponse(
        keyword_id=payload.keyword_id,
        video_count=video_count,
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
    task_ids, celery_task_ids, video_count = dispatch_update_category(
        db, payload.category_id, payload.limit, _enqueue_celery_task
    )
    return BatchUpdateTriggerResponse(
        category_id=payload.category_id,
        video_count=video_count,
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

    # 批量加载 video_ids 里出现的所有 video title(用于 update + crawl 精确显示)
    all_video_ids: set[int] = set()
    for t in tasks:
        if t.video_ids:
            try:
                ids = json.loads(t.video_ids)
                if isinstance(ids, list):
                    all_video_ids.update(int(x) for x in ids if x is not None)
            except (ValueError, TypeError):
                pass
    video_title_map: dict[int, str] = {}
    if all_video_ids:
        rows = db.query(Video.id, Video.title).filter(Video.id.in_(list(all_video_ids))).all()
        video_title_map = {r.id: (r.title or "") for r in rows}

    summaries: dict[int, str] = {}
    for t in tasks:
        kw_name = kw_map.get(t.keyword_id, "")
        count = t.videos_crawled or 0

        # 解析 video_ids 取第一个 ID 对应的标题
        first_title = ""
        if t.video_ids:
            try:
                ids = json.loads(t.video_ids)
                if isinstance(ids, list) and ids:
                    first_title = video_title_map.get(int(ids[0]), "")[:20]
            except (ValueError, TypeError):
                pass

        if t.task_type == "crawl":
            if count > 0 and first_title:
                summaries[t.id] = f"爬取了「{first_title}」等 {count} 个视频"
            elif count > 0:
                # 兜底:用 keyword 下最新视频
                fallback = first_video_map.get(t.keyword_id, "")[:20]
                if fallback:
                    summaries[t.id] = f"爬取了「{fallback}」等 {count} 个视频"
                else:
                    summaries[t.id] = f"爬取关键词「{kw_name}」,共 {count} 个视频"
            else:
                summaries[t.id] = f"爬取关键词「{kw_name}」"
        elif t.task_type == "update":
            if first_title:
                summaries[t.id] = f"更新了「{first_title}」"
            elif count == 1:
                summaries[t.id] = f"更新了关键词「{kw_name}」下 1 个视频"
            elif count > 1:
                summaries[t.id] = f"更新了关键词「{kw_name}」下 {count} 个视频"
            else:
                summaries[t.id] = f"更新关键词「{kw_name}」"
        elif t.task_type == "summary":
            # 大模型评论摘要任务
            if first_title:
                summaries[t.id] = f"生成了「{first_title}」的评论摘要"
            else:
                summaries[t.id] = "生成评论摘要"
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
