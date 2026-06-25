from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, Product
from app.schemas.product import ProductResponse

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def list_all_products(
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).order_by(Product.name))
    return list(result.scalars().all())


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: dict,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in data.items():
        if hasattr(product, field):
            setattr(product, field, value)

    await db.commit()
    return product


@router.put("/{product_id}/stock")
async def update_stock(
    product_id: int,
    quantity: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.product_service import ProductService
    service = ProductService(db)
    product = await service.update_stock(product_id, quantity)
    if not product:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await db.commit()
    return {
        "id": product.id,
        "name": product.name,
        "stock_quantity": product.stock_quantity,
    }
