from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Category, Keyword
from app.schemas.category import CategoryResponse

router = APIRouter(
    prefix="/categories",
    tags=["internal-categories"],
    dependencies=[Depends(verify_api_key)],
)
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: DbSession) -> list[CategoryResponse]:
    rows = (
        db.query(
            Category,
            func.count(Keyword.id).label("keyword_count"),
        )
        .outerjoin(
            Keyword,
            (Keyword.category_id == Category.id) & (Keyword.status != "deleted"),
        )
        .filter(Category.status == "active")
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )

    result: list[CategoryResponse] = []
    for category, count in rows:
        item = CategoryResponse.model_validate(category)
        item.keyword_count = int(count or 0)
        result.append(item)
    return result
