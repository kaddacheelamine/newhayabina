from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.enums import OrderStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    total_products = db.query(func.count(Product.id)).scalar() or 0

    orders_by_status = dict(
        db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )

    revenue = (
        db.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.status == OrderStatus.DELIVERED.value)
        .scalar()
    )

    best_sellers = (
        db.query(Product.id, Product.name, func.sum(OrderItem.quantity).label("units_sold"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    return {
        "total_products": total_products,
        "orders_by_status": orders_by_status,
        "revenue_delivered": float(revenue or 0),
        "best_sellers": [
            {"product_id": pid, "name": name, "units_sold": int(units)}
            for pid, name, units in best_sellers
        ],
    }
