from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Product, ProductImage
from app.schemas.product import ProductSearchParams


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id, Product.is_active == True)
            .options(selectinload(Product.images))
        )
        return result.scalar_one_or_none()

    async def get_by_pos_id(self, pos_product_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product).where(Product.pos_product_id == pos_product_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self, params: ProductSearchParams
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.is_active == True)

        if params.query:
            search_term = f"%{params.query}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.brand.ilike(search_term),
                    Product.category.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        if params.category:
            query = query.where(Product.category == params.category)

        if params.brand:
            query = query.where(Product.brand == params.brand)

        if params.min_price is not None:
            query = query.where(Product.selling_price >= params.min_price)

        if params.max_price is not None:
            query = query.where(Product.selling_price <= params.max_price)

        if params.is_alcoholic is not None:
            query = query.where(Product.is_alcoholic == params.is_alcoholic)

        if params.in_stock is not None:
            if params.in_stock:
                query = query.where(Product.stock_quantity > 0)
            else:
                query = query.where(Product.stock_quantity <= 0)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        sort_column = getattr(Product, params.sort_by, Product.name)
        if params.sort_order == "desc":
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        offset = (params.page - 1) * params.page_size
        query = (
            query.order_by(sort_column)
            .offset(offset)
            .limit(params.page_size)
            .options(selectinload(Product.images))
        )

        result = await self.db.execute(query)
        products = list(result.scalars().all())

        return products, total

    async def get_categories(self) -> list[str]:
        result = await self.db.execute(
            select(Product.category)
            .where(Product.is_active == True)
            .distinct()
            .order_by(Product.category)
        )
        return [row[0] for row in result.all()]

    async def get_brands(self) -> list[str]:
        result = await self.db.execute(
            select(Product.brand)
            .where(Product.is_active == True, Product.brand.isnot(None))
            .distinct()
            .order_by(Product.brand)
        )
        return [row[0] for row in result.all()]

    async def update_stock(
        self, product_id: int, quantity_change: int
    ) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        product.stock_quantity += quantity_change
        await self.db.flush()
        return product
