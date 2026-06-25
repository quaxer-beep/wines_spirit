from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.head_office import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    SupplierRatingCreate, SupplierRatingResponse,
    SupplierPerformance, PaginatedResponse,
)
from app.services.head_office.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Head Office - Suppliers"])


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(data: SupplierCreate, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    supplier = await service.create(data)
    await db.commit()
    return supplier


@router.get("", response_model=PaginatedResponse)
async def list_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    service = SupplierService(db)
    suppliers, total = await service.list(page, page_size, active_only)
    return {
        "items": [SupplierResponse.model_validate(s) for s in suppliers],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    supplier = await service.get(supplier_id)
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: int, data: SupplierUpdate, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    supplier = await service.update(supplier_id, data)
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    await db.commit()
    return supplier


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    deleted = await service.delete(supplier_id)
    if not deleted:
        raise HTTPException(404, "Supplier not found")
    await db.commit()


@router.post("/ratings", response_model=SupplierRatingResponse, status_code=201)
async def rate_supplier(data: SupplierRatingCreate, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    rating = await service.add_rating(data)
    await db.commit()
    return rating


@router.get("/{supplier_id}/performance", response_model=SupplierPerformance)
async def supplier_performance(supplier_id: int, db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    perf = await service.get_performance(supplier_id)
    if not perf:
        raise HTTPException(404, "Supplier not found")
    return perf


@router.get("/analytics/ranking", response_model=list[SupplierPerformance])
async def supplier_ranking(db: AsyncSession = Depends(get_db)):
    service = SupplierService(db)
    return await service.get_all_performance()
