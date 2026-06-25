from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    ProductListResponse,
    ProductResponse,
    ProductSearchParams,
)
from app.services.product_service import ProductService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProductListResponse])
async def search_products(
    query: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    is_alcoholic: bool | None = None,
    in_stock: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "name",
    sort_order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    params = ProductSearchParams(
        query=query,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        is_alcoholic=is_alcoholic,
        in_stock=in_stock,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    service = ProductService(db)
    products, total = await service.search(params)

    items = [
        ProductListResponse(
            id=p.id,
            name=p.name,
            brand=p.brand,
            category=p.category,
            selling_price=p.selling_price,
            unit=p.unit,
            is_alcoholic=p.is_alcoholic,
            stock_quantity=p.stock_quantity,
            primary_image=next(
                (img.url for img in p.images if img.is_primary),
                p.images[0].url if p.images else None,
            ),
        )
        for p in products
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    product = await service.get_by_id(product_id)
    if not product:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("/categories/list", response_model=list[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_categories()


@router.get("/brands/list", response_model=list[str])
async def get_brands(db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    return await service.get_brands()
