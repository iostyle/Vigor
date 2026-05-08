from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CategoryStatus = Literal["active", "inactive"]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    sort_order: int = Field(default=0, ge=0)
    status: CategoryStatus = "active"


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    sort_order: Optional[int] = Field(default=None, ge=0)
    status: Optional[CategoryStatus] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int
    status: str
    keyword_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
