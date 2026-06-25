from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

from src.config.settings import settings
from src.database.connection import db_manager

logger = logging.getLogger(__name__)


class ExportService:
    """Reads POS SQLite and writes per-branch SQLite files that the
    ecommerce sync service can consume."""

    EXPORTED_TABLES = {"products"}

    def export_all(self, output_dir: str | None = None) -> list[dict]:
        dst = Path(output_dir or settings.SYNC_EXPORT_DIR)
        dst.mkdir(parents=True, exist_ok=True)

        results: list[dict] = []
        with db_manager.get_session() as session:
            branches = (
                session.execute(
                    text("SELECT id, code, name FROM branches WHERE is_active = 1")
                )
                .fetchall()
            )

            for branch in branches:
                branch_id, code, name = branch
                export_path = dst / f"branch_{branch_id}.db"
                summary = self._export_one(session, branch_id, code, name, export_path)
                results.append(summary)

        return results

    def _export_one(self, session, branch_id: int, code: str, name: str, path: Path) -> dict:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        start = datetime.now(timezone.utc)
        row_count = 0

        try:
            conn.execute("DROP TABLE IF EXISTS products")
            conn.execute(
                """CREATE TABLE products (
                    id INTEGER,
                    name TEXT NOT NULL,
                    brand TEXT,
                    category TEXT,
                    description TEXT,
                    selling_price REAL NOT NULL DEFAULT 0,
                    cost_price REAL NOT NULL DEFAULT 0,
                    unit TEXT NOT NULL DEFAULT 'pcs',
                    reorder_level REAL NOT NULL DEFAULT 0,
                    stock_quantity REAL NOT NULL DEFAULT 0
                )"""
            )

            rows = session.execute(
                text("""SELECT
                    p.id,
                    p.name,
                    p.brand,
                    COALESCE(c.name, 'General') AS category,
                    NULL AS description,
                    p.selling_price,
                    p.cost_price,
                    p.unit,
                    p.reorder_level,
                    COALESCE(inv.quantity_on_hand, 0) AS stock_quantity
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                LEFT JOIN inventory inv ON inv.product_id = p.id AND inv.branch_id = :bid
                WHERE p.is_active = 1
                ORDER BY p.id"""),
                {"bid": branch_id},
            ).fetchall()

            for row in rows:
                conn.execute(
                    """INSERT INTO products
                    (id, name, brand, category, description,
                     selling_price, cost_price, unit, reorder_level, stock_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row.id,
                        row.name,
                        row.brand,
                        row.category,
                        None,
                        float(row.selling_price),
                        float(row.cost_price),
                        row.unit,
                        float(row.reorder_level),
                        float(row.stock_quantity),
                    ),
                )
                row_count += 1

            conn.commit()
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()

            summary = {
                "branch_id": branch_id,
                "branch_code": code,
                "branch_name": name,
                "path": str(path),
                "products_exported": row_count,
                "elapsed_seconds": round(elapsed, 2),
                "status": "ok",
            }
            logger.info(
                "Exported %d products for branch %s (%s) to %s (%.2fs)",
                row_count, code, name, path, elapsed,
            )

        except Exception as exc:
            conn.rollback()
            summary = {
                "branch_id": branch_id,
                "branch_code": code,
                "branch_name": name,
                "path": str(path),
                "products_exported": 0,
                "elapsed_seconds": 0,
                "status": "error",
                "error": str(exc),
            }
            logger.error("Export failed for branch %s: %s", code, exc)

        finally:
            conn.close()

        return summary
