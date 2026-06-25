from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    cart,
    checkout,
    customers,
    delivery,
    loyalty,
    mobile,
    notifications,
    orders,
    payments,
    products,
    promotions,
    rider,
    verification,
)
from app.api.v1.head_office import (
    alerts,
    dashboard,
    forecasts,
    goods_received,
    purchase_orders,
    reports,
    suppliers,
    transfers,
)

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
v1_router.include_router(verification.router, prefix="/customers", tags=["Customers - Verification"])
v1_router.include_router(products.router, prefix="/products", tags=["Products"])
v1_router.include_router(cart.router, prefix="/cart", tags=["Cart"])
v1_router.include_router(checkout.router, prefix="/checkout", tags=["Checkout"])
v1_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
v1_router.include_router(delivery.router, prefix="/delivery", tags=["Delivery"])
v1_router.include_router(loyalty.router, prefix="/loyalty", tags=["Loyalty"])
v1_router.include_router(promotions.router, prefix="/promotions", tags=["Promotions"])
v1_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
v1_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
v1_router.include_router(rider.router, prefix="/rider", tags=["Rider"])
v1_router.include_router(mobile.router, prefix="/mobile", tags=["Mobile Apps"])

# Phase 3: Head Office Management
v1_router.include_router(suppliers.router, prefix="/head-office", tags=["Head Office - Suppliers"])
v1_router.include_router(purchase_orders.router, prefix="/head-office", tags=["Head Office - Purchase Orders"])
v1_router.include_router(goods_received.router, prefix="/head-office", tags=["Head Office - Goods Received"])
v1_router.include_router(transfers.router, prefix="/head-office", tags=["Head Office - Stock Transfers"])
v1_router.include_router(dashboard.router, prefix="/head-office", tags=["Head Office - Dashboard"])
v1_router.include_router(forecasts.router, prefix="/head-office", tags=["Head Office - Forecasting"])
v1_router.include_router(alerts.router, prefix="/head-office", tags=["Head Office - Alerts"])
v1_router.include_router(reports.router, prefix="/head-office", tags=["Head Office - Reports"])
