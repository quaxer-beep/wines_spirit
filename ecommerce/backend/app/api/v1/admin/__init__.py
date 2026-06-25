from fastapi import APIRouter

from app.api.v1.admin import (
    analytics,
    compliance,
    delivery_fees,
    orders,
    products,
    promotions,
    riders,
    sync,
    users,
    verification,
)

router = APIRouter()

router.include_router(orders.router, prefix="/orders", tags=["Admin - Orders"])
router.include_router(products.router, prefix="/products", tags=["Admin - Products"])
router.include_router(riders.router, prefix="/riders", tags=["Admin - Riders"])
router.include_router(users.router, prefix="/users", tags=["Admin - Users"])
router.include_router(verification.router, prefix="/verification", tags=["Admin - Verification"])
router.include_router(promotions.router, prefix="/promotions", tags=["Admin - Promotions"])
router.include_router(delivery_fees.router, prefix="/delivery-fees", tags=["Admin - Delivery Fees"])
router.include_router(compliance.router, prefix="/compliance", tags=["Admin - Compliance"])
router.include_router(sync.router, prefix="/sync", tags=["Admin - Sync"])
router.include_router(analytics.router, prefix="/analytics", tags=["Admin - Analytics"])
