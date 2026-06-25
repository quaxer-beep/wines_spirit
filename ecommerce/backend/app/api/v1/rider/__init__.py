from fastapi import APIRouter

from app.api.v1.rider import deliveries

router = APIRouter()

router.include_router(deliveries.router, prefix="/deliveries", tags=["Rider - Deliveries"])
