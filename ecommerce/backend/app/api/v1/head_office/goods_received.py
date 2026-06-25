from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.head_office import GoodsReceivedNote, GoodsReceivedItem, Supplier, PurchaseOrder
from app.schemas.head_office import (
    GoodsReceivedNoteCreate, GoodsReceivedNoteResponse, GoodsReceivedItemResponse, PaginatedResponse,
)
from app.services.head_office.grn_service import GRNService

router = APIRouter(prefix="/goods-received", tags=["Head Office - Goods Received"])


@router.post("", response_model=GoodsReceivedNoteResponse, status_code=201)
async def create_grn(data: GoodsReceivedNoteCreate, db: AsyncSession = Depends(get_db)):
    service = GRNService(db)
    grn = await service.create(data)
    await db.commit()
    return await _enrich_grn(grn, db)


@router.get("", response_model=PaginatedResponse)
async def list_grns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = GRNService(db)
    grns, total = await service.list(page, page_size, supplier_id)
    items = [await _enrich_grn(grn, db) for grn in grns]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{grn_id}", response_model=GoodsReceivedNoteResponse)
async def get_grn(grn_id: int, db: AsyncSession = Depends(get_db)):
    service = GRNService(db)
    grn = await service.get(grn_id)
    if not grn:
        raise HTTPException(404, "Goods received note not found")
    return await _enrich_grn(grn, db)


async def _enrich_grn(grn: GoodsReceivedNote, db: AsyncSession) -> dict:
    data = GoodsReceivedNoteResponse.model_validate(grn).model_dump()
    supplier_result = await db.execute(select(Supplier).where(Supplier.id == grn.supplier_id))
    supplier = supplier_result.scalar_one_or_none()
    data["supplier_name"] = supplier.name if supplier else None

    po_result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == grn.purchase_order_id))
    po = po_result.scalar_one_or_none()
    data["po_number"] = po.po_number if po else None

    data["items"] = [GoodsReceivedItemResponse.model_validate(i).model_dump() for i in grn.items]
    return data
