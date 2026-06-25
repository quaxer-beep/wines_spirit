from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Product, ProductImage, ProductSyncLog

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_from_pos(self, branch_id: int, db_path: str) -> ProductSyncLog:
        log = ProductSyncLog(
            branch_id=branch_id,
            status="in_progress",
        )
        self.db.add(log)
        await self.db.flush()

        try:
            if not Path(db_path).exists():
                raise FileNotFoundError(f"POS database not found: {db_path}")

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
            )
            if not cursor.fetchone():
                raise ValueError("No 'products' table in POS database")

            cursor.execute(
                """SELECT id, name, brand, category, description,
                          selling_price, cost_price, unit, reorder_level,
                          stock_quantity
                   FROM products"""
            )
            pos_products = cursor.fetchall()
            conn.close()

            added = 0
            updated = 0

            for pos_p in pos_products:
                existing = await self.db.execute(
                    select(Product).where(
                        Product.pos_product_id == pos_p["id"],
                        Product.branch_id == branch_id,
                    )
                )
                product = existing.scalar_one_or_none()

                product_data = {
                    "pos_product_id": pos_p["id"],
                    "name": pos_p["name"],
                    "brand": pos_p.get("brand"),
                    "category": pos_p.get("category", "General"),
                    "description": pos_p.get("description"),
                    "selling_price": float(pos_p["selling_price"]),
                    "cost_price": float(pos_p.get("cost_price", 0)),
                    "unit": pos_p.get("unit", "pcs"),
                    "reorder_level": int(pos_p.get("reorder_level", 0)),
                    "stock_quantity": int(pos_p.get("stock_quantity", 0)),
                    "branch_id": branch_id,
                    "is_active": True,
                }

                if product:
                    for field, value in product_data.items():
                        setattr(product, field, value)
                    product.updated_at = datetime.now(timezone.utc)
                    updated += 1
                else:
                    product = Product(**product_data)
                    self.db.add(product)
                    added += 1

            await self.db.flush()

            log.products_synced = added + updated
            log.products_added = added
            log.products_updated = updated
            log.status = "success"
            log.synced_at = datetime.now(timezone.utc)
            await self.db.flush()

            logger.info(
                f"Synced branch {branch_id}: {added} added, {updated} updated"
            )

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            await self.db.flush()
            logger.error(f"Sync failed for branch {branch_id}: {e}")

        return log

    async def sync_all_branches(self) -> list[ProductSyncLog]:
        logs = []
        base_path = Path(settings.POS_DATABASE_PATH)

        for db_file in base_path.glob("branch_*.db"):
            try:
                branch_id = int(db_file.stem.split("_")[1])
                log = await self.sync_from_pos(branch_id, str(db_file))
                logs.append(log)
            except (ValueError, IndexError):
                logger.warning(f"Skipping invalid POS DB file: {db_file}")

        return logs

    async def get_sync_history(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[ProductSyncLog], int]:
        from sqlalchemy import func

        query = (
            select(ProductSyncLog)
            .order_by(ProductSyncLog.synced_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
