from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models.comment import CommentSummary
from app.models.keyword import Keyword
from app.models.video import Video
from pydantic import BaseModel

from app.schemas.video import VideoListResponse, VideoResponse
from app.models.task import CrawlTask

router = APIRouter(
    prefix="/api/admin/videos",
    tags=["admin-videos"],
    dependencies=[Depends(verify_api_key)],
)

TimeWindow = Literal["24h", "7d", "30d", "all"]
SortField = Literal["heat_score", "publish_time", "like_count", "comment_count", "crawled_at"]
SortOrder = Literal["asc", "desc"]
VideoStatus = Literal["active", "hidden", "archived"]
VideoStatusFilter = Literal["active", "hidden", "archived", "all"]


class VideoStatusUpdate(BaseModel):
    status: VideoStatus


class SummaryTaskStatusResponse(BaseModel):
    task_id: int | None = None
    status: str | None = None
    is_running: bool = False


_TIME_WINDOW_DELTAS: dict[str, Optional[timedelta]] = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "all": None,
}
_PLATFORM_ALIASES = {"dy": "douyin", "bili": "bilibili"}


def _normalize_platform(platform: Optional[str]) -> Optional[str]:
    if platform is None:
        return None
    key = platform.strip().lower()
    return _PLATFORM_ALIASES.get(key, key)


def _apply_time_window(query, time_window: TimeWindow):
    delta = _TIME_WINDOW_DELTAS.get(time_window)
    if delta is None:
        return query
    cutoff = datetime.now() - delta
    return query.filter(Video.publish_time >= cutoff)


def _build_video_response(video: Video, summary: Optional[CommentSummary]) -> VideoResponse:
    comment_summary = None
    if summary is not None:
        keywords: list[str] = []
        if summary.top_keywords:
            keywords = [k.strip() for k in summary.top_keywords.split(",") if k.strip()]
        comment_summary = {
            "summary": summary.summary or "",
            "top_keywords": keywords,
            "sentiment": summary.sentiment or "neutral",
            "generated_at": summary.generated_at,
            "comment_count": summary.comment_count or 0,
        }

    return VideoResponse.model_validate(
        {
            "id": video.id,
            "external_id": video.external_id,
            "platform": video.platform,
            "status": video.status or "active",
            "title": video.title,
            "author_name": video.author_name,
            "cover_url": video.cover_url,
            "video_url": video.video_url,
            "like_count": video.like_count or 0,
            "comment_count": video.comment_count or 0,
            "share_count": video.share_count or 0,
            "heat_score": video.heat_score,
            "publish_time": video.publish_time,
            "crawled_at": video.crawled_at,
            "last_updated_at": video.last_updated_at,
            "summary": video.summary,
            "tags": video.tags,
            "comment_summary": comment_summary,
        }
    )


@router.get("", response_model=VideoListResponse)
def list_videos(
    keyword_id: Optional[int] = Query(None, ge=1),
    platform: Optional[str] = Query(None, max_length=16),
    video_status: VideoStatusFilter = Query("all"),
    time_window: TimeWindow = Query("all"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: SortField = Query("heat_score"),
    order: SortOrder = Query("desc"),
    db: Session = Depends(get_db),
) -> VideoListResponse:
    # Why: 过滤掉非 active 关键词(如 deleted)下的视频,用户不希望看到
    query = (
        db.query(Video)
        .join(Keyword, Video.keyword_id == Keyword.id)
        .filter(Keyword.status == "active")
    )

    if keyword_id is not None:
        query = query.filter(Video.keyword_id == keyword_id)

    normalized_platform = _normalize_platform(platform)
    if normalized_platform is not None:
        query = query.filter(Video.platform == normalized_platform)

    if video_status != "all":
        query = query.filter(Video.status == video_status)

    query = _apply_time_window(query, time_window)

    total = query.count()

    sort_column = getattr(Video, sort)
    direction = desc if order == "desc" else asc
    query = query.order_by(direction(sort_column).nullslast() if order == "desc" else direction(sort_column).nullsfirst())

    videos = query.offset(offset).limit(limit).all()

    video_ids = [v.id for v in videos]
    summaries: dict[int, CommentSummary] = {}
    if video_ids:
        rows = (
            db.query(CommentSummary)
            .filter(CommentSummary.video_id.in_(video_ids))
            .all()
        )
        summaries = {row.video_id: row for row in rows}

    data = [_build_video_response(v, summaries.get(v.id)) for v in videos]
    return VideoListResponse(total=total, data=data)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
) -> VideoResponse:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    summary = (
        db.query(CommentSummary)
        .filter(CommentSummary.video_id == video_id)
        .first()
    )
    return _build_video_response(video, summary)


@router.patch("/{video_id}/status", response_model=VideoResponse)
def update_video_status(
    video_id: int,
    payload: VideoStatusUpdate,
    db: Session = Depends(get_db),
) -> VideoResponse:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    video.status = payload.status
    db.add(video)
    db.commit()
    db.refresh(video)

    summary = (
        db.query(CommentSummary)
        .filter(CommentSummary.video_id == video_id)
        .first()
    )
    return _build_video_response(video, summary)


@router.post("/{video_id}/update", status_code=status.HTTP_202_ACCEPTED)
def trigger_video_update(
    video_id: int,
    db: Session = Depends(get_db),
) -> dict:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    from app.celery_app import celery_app

    result = celery_app.send_task(
        "app.tasks.updater.update_single_video",
        args=[video_id],
        queue="updater",
    )
    return {"status": "accepted", "task_id": result.id, "video_id": video_id}


@router.post("/{video_id}/generate-summary", status_code=status.HTTP_202_ACCEPTED)
def trigger_generate_summary(
    video_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """手动触发视频评论摘要生成,落 CrawlTask 行 + 派发 Celery。"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    # Why: 在任务历史里能看到摘要生成任务,沿用 CrawlTask 表
    import json
    from app.models.task import CrawlTask

    task = CrawlTask(
        keyword_id=video.keyword_id,
        video_ids=json.dumps([video_id]),
        task_type="summary",
        source="manual",
        status="pending",
        videos_crawled=0,
        started_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    from app.tasks.processor import generate_summary_task

    result = generate_summary_task.delay(video_id, task.id)
    return {
        "task_id": task.id,
        "celery_task_id": result.id,
        "status": "pending",
    }


@router.get("/{video_id}/summary-task", response_model=SummaryTaskStatusResponse)
def get_summary_task_status(
    video_id: int,
    db: Session = Depends(get_db),
) -> SummaryTaskStatusResponse:
    video = db.query(Video.id).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    task = (
        db.query(CrawlTask)
        .filter(CrawlTask.task_type == "summary")
        .filter(CrawlTask.video_ids == f"[{video_id}]")
        .order_by(CrawlTask.id.desc())
        .first()
    )
    if task is None:
        return SummaryTaskStatusResponse()

    return SummaryTaskStatusResponse(
        task_id=task.id,
        status=task.status,
        is_running=task.status in {"pending", "running"},
    )
