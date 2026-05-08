from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Category, Keyword
from app.schemas.keyword import KeywordCreate, KeywordResponse, KeywordUpdate

router = APIRouter(prefix="/keywords", tags=["admin-keywords"], dependencies=[Depends(verify_api_key)])
DbSession = Annotated[Session, Depends(get_db)]


def _get_keyword_or_404(db: Session, keyword_id: int) -> Keyword:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None or keyword.status == "deleted":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")
    return keyword


def _require_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category {category_id} not found",
        )
    return category


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
def create_keyword(payload: KeywordCreate, db: DbSession) -> Keyword:
    _require_category(db, payload.category_id)
    keyword = Keyword(
        category_id=payload.category_id,
        keyword=payload.keyword,
        platform=payload.platform,
        status="active",
        crawl_threshold=payload.crawl_threshold,
        priority=payload.priority,
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.get("", response_model=list[KeywordResponse])
def list_keywords(
    db: DbSession,
    category_id: int | None = Query(None, ge=1),
    platform: str | None = Query(None, max_length=20),
    limit: int = 100,
    offset: int = 0,
) -> list[Keyword]:
    query = db.query(Keyword).filter(Keyword.status != "deleted")
    if category_id is not None:
        query = query.filter(Keyword.category_id == category_id)
    if platform is not None:
        query = query.filter(Keyword.platform == platform)
    return query.order_by(Keyword.id.asc()).offset(offset).limit(limit).all()


@router.put("/{keyword_id}", response_model=KeywordResponse)
def update_keyword(keyword_id: int, payload: KeywordUpdate, db: DbSession) -> Keyword:
    keyword = _get_keyword_or_404(db, keyword_id)

    updates = payload.model_dump(exclude_unset=True)
    if "category_id" in updates:
        _require_category(db, updates["category_id"])
    for field, value in updates.items():
        setattr(keyword, field, value)

    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}", response_model=KeywordResponse)
def delete_keyword(keyword_id: int, db: DbSession) -> Keyword:
    keyword = _get_keyword_or_404(db, keyword_id)
    keyword.status = "deleted"
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword
