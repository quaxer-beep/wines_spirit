from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampMixin


class ProductImageResponse(BaseModel):
    id: int
    url: str
    is_primary: bool = False
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str
    brand: str | None = None
    category: str
    description: str | None = None
    selling_price: float
    cost_price: float = 0
    unit: str = "pcs"
    is_alcoholic: bool = True
    requires_age_verification: bool = True
    stock_quantity: int = 0


class ProductResponse(ProductBase, TimestampMixin):
    id: int
    pos_product_id: int | None = None
    reorder_level: int = 0
    is_active: bool = True
    branch_id: int | None = None
    images: list[ProductImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    id: int
    name: str
    brand: str | None = None
    category: str
    selling_price: float
    unit: str
    is_alcoholic: bool
    stock_quantity: int
    primary_image: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductSearchParams(BaseModel):
    query: str | None = None
    category: str | None = None
    brand: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    is_alcoholic: bool | None = None
    in_stock: bool | None = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "name"
    sort_order: str = "asc"
