from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.models import Category, Keyword
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(
    prefix="/categories",
    tags=["admin-categories"],
    dependencies=[Depends(verify_api_key)],
)
DbSession = Annotated[Session, Depends(get_db)]


def _get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


def _with_keyword_count(db: Session, category: Category) -> CategoryResponse:
    count = (
        db.query(func.count(Keyword.id))
        .filter(Keyword.category_id == category.id, Keyword.status != "deleted")
        .scalar()
        or 0
    )
    data = CategoryResponse.model_validate(category)
    data.keyword_count = int(count)
    return data


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: DbSession) -> CategoryResponse:
    if db.query(Category).filter(Category.name == payload.name).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists",
        )

    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return _with_keyword_count(db, category)


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: DbSession) -> list[CategoryResponse]:
    categories = (
        db.query(Category)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )
    return [_with_keyword_count(db, c) for c in categories]


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: DbSession) -> CategoryResponse:
    category = _get_category_or_404(db, category_id)
    return _with_keyword_count(db, category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, payload: CategoryUpdate, db: DbSession
) -> CategoryResponse:
    category = _get_category_or_404(db, category_id)

    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] != category.name:
        exists = (
            db.query(Category)
            .filter(Category.name == updates["name"], Category.id != category_id)
            .first()
        )
        if exists is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{updates['name']}' already exists",
            )

    for field, value in updates.items():
        setattr(category, field, value)

    db.add(category)
    db.commit()
    db.refresh(category)
    return _with_keyword_count(db, category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DbSession) -> None:
    category = _get_category_or_404(db, category_id)

    # 3B: 有关键词关联时禁止删除
    has_keywords = (
        db.query(Keyword)
        .filter(Keyword.category_id == category_id, Keyword.status != "deleted")
        .first()
    )
    if has_keywords is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete category with active keywords",
        )

    db.delete(category)
    db.commit()
