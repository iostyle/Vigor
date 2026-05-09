from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Keyword, Video

router = APIRouter(
    prefix="/stats",
    tags=["internal-stats"],
    dependencies=[Depends(verify_api_key)],
)


class KeywordStatsResponse(BaseModel):
    keyword_id: int
    keyword: str
    video_count: int
    avg_heat_score: float


class TrendStatsResponse(BaseModel):
    date: str
    video_count: int
    avg_heat_score: float


class TodayStatsResponse(BaseModel):
    date: str
    total: int
    by_platform: dict[str, int]


@router.get("/keywords", response_model=list[KeywordStatsResponse])
def list_keyword_stats(db: Session = Depends(get_db)) -> list[KeywordStatsResponse]:
    rows = (
        db.query(
            Keyword.id.label("keyword_id"),
            Keyword.keyword.label("keyword"),
            func.count(Video.id).label("video_count"),
            func.round(func.avg(Video.heat_score), 1).label("avg_heat_score"),
        )
        .join(Video, Video.keyword_id == Keyword.id)
        .group_by(Keyword.id, Keyword.keyword)
        .order_by(Keyword.id.asc())
        .all()
    )

    return [
        KeywordStatsResponse(
            keyword_id=row.keyword_id,
            keyword=row.keyword,
            video_count=row.video_count,
            avg_heat_score=float(row.avg_heat_score or 0.0),
        )
        for row in rows
    ]


@router.get("/trends", response_model=list[TrendStatsResponse])
def list_trends(db: Session = Depends(get_db)) -> list[TrendStatsResponse]:
    start_time = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(
            func.date(Video.publish_time).label("date"),
            func.count(Video.id).label("video_count"),
            func.round(func.avg(Video.heat_score), 1).label("avg_heat_score"),
        )
        .filter(Video.publish_time >= start_time)
        .group_by(func.date(Video.publish_time))
        .order_by(func.date(Video.publish_time).asc())
        .all()
    )

    return [
        TrendStatsResponse(
            date=str(row.date),
            video_count=row.video_count,
            avg_heat_score=float(row.avg_heat_score or 0.0),
        )
        for row in rows
    ]


@router.get("/today", response_model=TodayStatsResponse)
def get_today_stats(db: Session = Depends(get_db)) -> TodayStatsResponse:
    """今日(UTC)新增视频数,按 crawled_at 落在当日 0:00 到现在统计。"""
    now = datetime.utcnow()
    # Why: 截断到 UTC 当日 0 点;crawled_at 在 DB 里就是 UTC
    start = datetime(now.year, now.month, now.day)

    total = (
        db.query(func.count(Video.id))
        .filter(Video.crawled_at >= start)
        .scalar()
        or 0
    )

    rows = (
        db.query(Video.platform, func.count(Video.id))
        .filter(Video.crawled_at >= start)
        .group_by(Video.platform)
        .all()
    )
    by_platform = {platform: int(count) for platform, count in rows}

    return TodayStatsResponse(
        date=start.strftime("%Y-%m-%d"),
        total=int(total),
        by_platform=by_platform,
    )
