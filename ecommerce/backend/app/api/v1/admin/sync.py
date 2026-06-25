from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pathlib import Path

from app.api.deps import get_admin_user, get_db
from app.core.config import settings
from app.models.customer import Customer
from app.services.sync_service import SyncService

router = APIRouter()


@router.post("/run")
async def run_sync(
    branch_id: int | None = None,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = SyncService(db)
    if branch_id:
        db_path = str(Path(settings.POS_DATABASE_PATH) / f"branch_{branch_id}.db")
        log = await service.sync_from_pos(branch_id, db_path)
    else:
        logs = await service.sync_all_branches()
        await db.commit()
        return {
            "message": f"Synced {len(logs)} branches",
            "logs": [
                {
                    "branch_id": l.branch_id,
                    "status": l.status,
                    "added": l.products_added,
                    "updated": l.products_updated,
                }
                for l in logs
            ],
        }

    await db.commit()
    return {
        "message": "Sync completed",
        "branch_id": log.branch_id,
        "status": log.status,
        "added": log.products_added,
        "updated": log.products_updated,
    }


@router.get("/history")
async def sync_history(
    page: int = 1,
    page_size: int = 20,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = SyncService(db)
    logs, total = await service.get_sync_history(page, page_size)
    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }
