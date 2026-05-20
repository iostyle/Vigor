from datetime import datetime, timedelta
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key, verify_api_key_value
from app.config import settings
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
_PLATFORM_ALIASES = {"dy": "douyin", "bili": "bilibili"}


def _normalize_platform(platform: Optional[str]) -> Optional[str]:
    if platform is None:
        return None
    key = platform.strip().lower()
    return _PLATFORM_ALIASES.get(key, key)


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

    normalized_platform = _normalize_platform(platform)
    if normalized_platform is not None:
        query = query.filter(Video.platform == normalized_platform)

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


def _proxy_headers(range_header: Optional[str]) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "Referer": "https://www.douyin.com/",
        "Cookie": settings.DOUYIN_COOKIES,
    }
    if range_header:
        headers["Range"] = range_header
    return headers


@router.get("/{video_id}/stream")
def stream_video(
    video_id: int,
    api_key: Optional[str] = Query(None),
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db),
) -> Response:
    verify_api_key_value(api_key)
    video = _get_video_or_404(db, video_id)
    if video.platform != "douyin" or not video.video_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video stream not available",
        )
    if ".mp3" in video.video_url.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video stream not available",
        )

    client = httpx.Client(timeout=30.0, follow_redirects=True)
    request = client.build_request(
        "GET",
        video.video_url,
        headers=_proxy_headers(range_header),
    )
    upstream = client.send(request, stream=True)
    upstream.raise_for_status()

    headers = {}
    for key in ("content-range", "accept-ranges", "content-length"):
        value = upstream.headers.get(key)
        if value:
            headers[key] = value
    headers.setdefault("accept-ranges", "bytes")

    def _iter_stream():
        try:
            for chunk in upstream.iter_bytes():
                if chunk:
                    yield chunk
        finally:
            upstream.close()
            client.close()

    return StreamingResponse(
        _iter_stream(),
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "video/mp4"),
        headers=headers,
    )


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
