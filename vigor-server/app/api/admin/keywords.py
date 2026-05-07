from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Keyword
from app.schemas.keyword import KeywordCreate, KeywordResponse, KeywordUpdate

router = APIRouter(prefix="/keywords", tags=["admin-keywords"], dependencies=[Depends(verify_api_key)])
DbSession = Annotated[Session, Depends(get_db)]


def _get_keyword_or_404(db: Session, keyword_id: int) -> Keyword:
    keyword = db.get(Keyword, keyword_id)
    if keyword is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")
    return keyword


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
def create_keyword(payload: KeywordCreate, db: DbSession) -> Keyword:
    keyword = Keyword(
        keyword=payload.keyword,
        category=payload.category,
        status="active",
        crawl_threshold=payload.crawl_threshold,
        priority=payload.priority,
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.get("", response_model=list[KeywordResponse])
def list_keywords(db: DbSession) -> list[Keyword]:
    return db.query(Keyword).filter(Keyword.status != "deleted").order_by(Keyword.id.asc()).all()


@router.put("/{keyword_id}", response_model=KeywordResponse)
def update_keyword(keyword_id: int, payload: KeywordUpdate, db: DbSession) -> Keyword:
    keyword = _get_keyword_or_404(db, keyword_id)

    updates = payload.model_dump(exclude_unset=True)
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
