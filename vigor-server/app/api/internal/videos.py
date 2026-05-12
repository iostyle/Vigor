from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Comment, CommentSummary, Keyword, Video
from app.schemas import (
    CommentResponse,
    CommentSummaryResponse,
    VideoListResponse,
    VideoResponse,
)

router = APIRouter(
    prefix="/videos",
    tags=["internal-videos"],
    dependencies=[Depends(verify_api_key)],
)

TimeWindow = Literal["1d", "3d", "7d", "15d", "30d"]
SortField = Literal["heat_score", "publish_time"]

_TIME_WINDOW_DAYS = {"1d": 1, "3d": 3, "7d": 7, "15d": 15, "30d": 30}


@router.get("", response_model=VideoListResponse)
def list_videos(
    keyword_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None, max_length=16),
    time_window: Optional[TimeWindow] = Query(None),
    sort: SortField = Query("heat_score"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> VideoListResponse:
    # Why: 过滤非 active 关键词(如 deleted)下的视频。统一在最外层 join,
    # 避免 category_id 分支重复 join 触发 SQLAlchemy 'already joined' 错误
    query = (
        db.query(Video)
        .join(Keyword, Video.keyword_id == Keyword.id)
        .filter(Keyword.status == "active")
        .filter(Video.status == "active")
    )

    if keyword_id is not None:
        query = query.filter(Video.keyword_id == keyword_id)

    if category_id is not None:
        query = query.filter(Keyword.category_id == category_id)

    if platform is not None:
        query = query.filter(Video.platform == platform)

    if time_window is not None:
        cutoff = datetime.utcnow() - timedelta(days=_TIME_WINDOW_DAYS[time_window])
        query = query.filter(Video.publish_time >= cutoff)

    total = query.count()

    sort_col = Video.heat_score if sort == "heat_score" else Video.publish_time
    rows = query.order_by(sort_col.desc().nullslast()).offset(offset).limit(limit).all()

    # Why: 一次 IN 把本页所有 CommentSummary 取回,避免 N+1
    summary_map: dict[int, CommentSummary] = {}
    if rows:
        summary_rows = (
            db.query(CommentSummary)
            .filter(CommentSummary.video_id.in_([v.id for v in rows]))
            .all()
        )
        summary_map = {s.video_id: s for s in summary_rows}

    data: list[VideoResponse] = []
    for v in rows:
        resp = VideoResponse.model_validate(v)
        s = summary_map.get(v.id)
        if s is not None:
            resp = _apply_summary_row(resp, s)
        data.append(resp)

    return VideoListResponse(total=total, data=data)


def _get_video_or_404(db: Session, video_id: int) -> Video:
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


def _apply_summary_row(
    response: VideoResponse, summary_row: CommentSummary
) -> VideoResponse:
    """把一条 CommentSummary 行填到 VideoResponse.comment_summary。

    top_keywords 在 DB 里是 JSON 字符串,这里 json.loads 成 list;
    兼容历史数据:逗号分隔的旧字符串也能解析。
    """
    top_keywords: list[str] = []
    if summary_row.top_keywords:
        import json

        try:
            parsed = json.loads(summary_row.top_keywords)
            if isinstance(parsed, list):
                top_keywords = [str(item) for item in parsed]
        except (ValueError, TypeError):
            top_keywords = [
                s.strip() for s in summary_row.top_keywords.split(",") if s.strip()
            ]

    response.comment_summary = CommentSummaryResponse(
        summary=summary_row.summary or "",
        top_keywords=top_keywords,
        sentiment=summary_row.sentiment or "neutral",
        generated_at=summary_row.generated_at or datetime.utcnow(),
        comment_count=summary_row.comment_count or 0,
    )
    return response


def _attach_comment_summary(
    db: Session, video: Video, response: VideoResponse
) -> VideoResponse:
    """单条视频:查 CommentSummary 并挂到 response。"""
    summary_row = (
        db.query(CommentSummary)
        .filter(CommentSummary.video_id == video.id)
        .first()
    )
    if summary_row is None:
        return response
    return _apply_summary_row(response, summary_row)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int, db: Session = Depends(get_db)
) -> VideoResponse:
    video = _get_video_or_404(db, video_id)
    response = VideoResponse.model_validate(video)
    return _attach_comment_summary(db, video, response)


@router.get("/{video_id}/comments", response_model=list[CommentResponse])
def list_video_comments(
    video_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    _get_video_or_404(db, video_id)
    rows = (
        db.query(Comment)
        .filter(Comment.video_id == video_id)
        .order_by(Comment.like_count.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [CommentResponse.model_validate(c) for c in rows]


@router.get("/{video_id}/summary", response_model=VideoResponse)
def get_video_summary(
    video_id: int, db: Session = Depends(get_db)
) -> VideoResponse:
    video = _get_video_or_404(db, video_id)
    response = VideoResponse.model_validate(video)
    return _attach_comment_summary(db, video, response)
