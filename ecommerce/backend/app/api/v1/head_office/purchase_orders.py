from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.head_office import PurchaseOrder, Supplier
from app.schemas.head_office import (
    PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderItemResponse, PaginatedResponse,
)
from app.services.head_office.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Head Office - Purchase Orders"])


@router.post("", response_model=PurchaseOrderResponse, status_code=201)
async def create_po(data: PurchaseOrderCreate, db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.create(data)
    await db.commit()
    return await _enrich_po(po, db)


@router.get("", response_model=PaginatedResponse)
async def list_pos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    supplier_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = PurchaseOrderService(db)
    pos, total = await service.list(page, page_size, status, supplier_id)
    items = [await _enrich_po(po, db) for po in pos]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_po(po_id: int, db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.get(po_id)
    if not po:
        raise HTTPException(404, "Purchase order not found")
    return await _enrich_po(po, db)


@router.post("/{po_id}/submit", response_model=PurchaseOrderResponse)
async def submit_po(po_id: int, db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.submit(po_id)
    if not po:
        raise HTTPException(400, "Cannot submit purchase order in current status")
    await db.commit()
    return await _enrich_po(po, db)


@router.post("/{po_id}/approve", response_model=PurchaseOrderResponse)
async def approve_po(po_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.approve(po_id, user_id)
    if not po:
        raise HTTPException(400, "Cannot approve purchase order in current status")
    await db.commit()
    return await _enrich_po(po, db)


@router.post("/{po_id}/receive", response_model=PurchaseOrderResponse)
async def receive_po(po_id: int, delivery_date: date | None = Query(None), db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.receive(po_id, delivery_date)
    if not po:
        raise HTTPException(400, "Cannot receive purchase order in current status")
    await db.commit()
    return await _enrich_po(po, db)


@router.post("/{po_id}/cancel", response_model=PurchaseOrderResponse)
async def cancel_po(po_id: int, db: AsyncSession = Depends(get_db)):
    service = PurchaseOrderService(db)
    po = await service.cancel(po_id)
    if not po:
        raise HTTPException(400, "Cannot cancel purchase order in current status")
    await db.commit()
    return await _enrich_po(po, db)


async def _enrich_po(po: PurchaseOrder, db: AsyncSession) -> dict:
    data = PurchaseOrderResponse.model_validate(po).model_dump()
    supplier_result = await db.execute(
        __import__("sqlalchemy").select(Supplier).where(Supplier.id == po.supplier_id)
    )
    supplier = supplier_result.scalar_one_or_none()
    data["supplier_name"] = supplier.name if supplier else None
    data["items"] = [PurchaseOrderItemResponse.model_validate(i).model_dump() for i in po.items]
    return data
