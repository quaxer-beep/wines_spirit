from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, Order, OrderItem, Product

router = APIRouter()


@router.get("/dashboard")
async def dashboard(
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_orders = await db.execute(
        select(func.count()).select_from(Order)
    )
    total_orders = total_orders.scalar() or 0

    today_orders = await db.execute(
        select(func.count()).select_from(
            select(Order).where(Order.created_at >= today).subquery()
        )
    )
    today_orders = today_orders.scalar() or 0

    total_revenue = await db.execute(
        select(func.coalesce(func.sum(Order.grand_total), 0))
        .where(Order.payment_status == "paid")
    )
    total_revenue = float(total_revenue.scalar() or 0)

    today_revenue = await db.execute(
        select(func.coalesce(func.sum(Order.grand_total), 0))
        .where(
            Order.payment_status == "paid",
            Order.created_at >= today,
        )
    )
    today_revenue = float(today_revenue.scalar() or 0)

    pending_orders = await db.execute(
        select(func.count()).select_from(
            select(Order).where(Order.status == "pending").subquery()
        )
    )
    pending_orders = pending_orders.scalar() or 0

    processing_orders = await db.execute(
        select(func.count()).select_from(
            select(Order)
            .where(Order.status.in_(["confirmed", "processing"]))
            .subquery()
        )
    )
    processing_orders = processing_orders.scalar() or 0

    top_products_result = await db.execute(
        select(
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_sold"),
        )
        .select_from(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
    )
    top_products = [
        {"name": row[0], "total_sold": int(row[1])}
        for row in top_products_result.all()
    ]

    return {
        "total_orders": total_orders,
        "today_orders": today_orders,
        "total_revenue": round(total_revenue, 2),
        "today_revenue": round(today_revenue, 2),
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "top_products": top_products,
        "period": {
            "today": today.isoformat(),
            "week_ago": week_ago.isoformat(),
            "month_ago": month_ago.isoformat(),
        },
    }


@router.get("/revenue")
async def revenue_analytics(
    days: int = 30,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Order.created_at).label("date"),
            func.count().label("orders"),
            func.coalesce(func.sum(Order.grand_total), 0).label("revenue"),
        )
        .where(
            Order.payment_status == "paid",
            Order.created_at >= since,
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    return {
        "days": days,
        "data": [
            {
                "date": str(row[0]),
                "orders": int(row[1]),
                "revenue": float(row[2]),
            }
            for row in result.all()
        ],
    }
