from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.head_office import (
    StockTransferCreate, StockTransferResponse, StockTransferItemResponse, PaginatedResponse,
)
from app.services.head_office.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["Head Office - Stock Transfers"])


@router.post("", response_model=StockTransferResponse, status_code=201)
async def create_transfer(data: StockTransferCreate, db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfer = await service.create(data)
    await db.commit()
    return _enrich_transfer(transfer)


@router.get("", response_model=PaginatedResponse)
async def list_transfers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    branch_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = TransferService(db)
    transfers, total = await service.list(page, page_size, status, branch_id)
    items = [_enrich_transfer(t) for t in transfers]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{transfer_id}", response_model=StockTransferResponse)
async def get_transfer(transfer_id: int, db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfer = await service.get(transfer_id)
    if not transfer:
        raise HTTPException(404, "Stock transfer not found")
    return _enrich_transfer(transfer)


@router.post("/{transfer_id}/approve", response_model=StockTransferResponse)
async def approve_transfer(transfer_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfer = await service.approve(transfer_id, user_id)
    if not transfer:
        raise HTTPException(400, "Cannot approve transfer in current status")
    await db.commit()
    return _enrich_transfer(transfer)


@router.post("/{transfer_id}/dispatch", response_model=StockTransferResponse)
async def dispatch_transfer(transfer_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfer = await service.dispatch(transfer_id, user_id)
    if not transfer:
        raise HTTPException(400, "Cannot dispatch transfer in current status")
    await db.commit()
    return _enrich_transfer(transfer)


@router.post("/{transfer_id}/receive", response_model=StockTransferResponse)
async def receive_transfer(transfer_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfer = await service.receive(transfer_id, user_id)
    if not transfer:
        raise HTTPException(400, "Cannot receive transfer in current status")
    await db.commit()
    return _enrich_transfer(transfer)


@router.post("/{transfer_id}/reject", response_model=StockTransferResponse)
async def reject_transfer(
    transfer_id: int,
    reason: str = Query(...),
    user_id: int = Query(1),
    db: AsyncSession = Depends(get_db),
):
    service = TransferService(db)
    transfer = await service.reject(transfer_id, user_id, reason)
    if not transfer:
        raise HTTPException(400, "Cannot reject transfer in current status")
    await db.commit()
    return _enrich_transfer(transfer)


@router.get("/pending/{branch_id}", response_model=list[StockTransferResponse])
async def pending_transfers(branch_id: int, db: AsyncSession = Depends(get_db)):
    service = TransferService(db)
    transfers = await service.get_pending_for_branch(branch_id)
    return [_enrich_transfer(t) for t in transfers]


def _enrich_transfer(transfer) -> dict:
    data = StockTransferResponse.model_validate(transfer).model_dump()
    data["items"] = [StockTransferItemResponse.model_validate(i).model_dump() for i in transfer.items]
    return data
