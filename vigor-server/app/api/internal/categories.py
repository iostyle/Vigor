from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Keyword

router = APIRouter(
    prefix="/categories",
    tags=["internal-categories"],
    dependencies=[Depends(verify_api_key)],
)


class CategoryResponse(BaseModel):
    category: str
    keyword_count: int


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryResponse]:
    rows = (
        db.query(
            Keyword.category.label("category"),
            func.count(Keyword.id).label("keyword_count"),
        )
        .filter(Keyword.category.isnot(None))
        .filter(Keyword.status == "active")
        .group_by(Keyword.category)
        .order_by(func.count(Keyword.id).desc())
        .all()
    )

    return [
        CategoryResponse(category=row.category, keyword_count=row.keyword_count)
        for row in rows
    ]
