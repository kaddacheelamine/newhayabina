from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.admin import Admin
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """Public endpoint -- no auth required. Used by customers at checkout."""
    return order_service.create_order(db, payload)


@router.get("", response_model=list[OrderOut])
def list_orders(status_filter: str | None = None, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return order_service.list_orders(db, status_filter=status_filter)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return order_service.get_order_or_404(db, order_id)


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Updates order status. This is the only way to change an order's
    status -- it's what triggers stock deduction (on -> CONFIRMED) or
    stock restoration (on -> CANCELLED after stock was already deducted)."""
    order = order_service.get_order_or_404(db, order_id)
    return order_service.update_order_status(
        db, order, payload.status.value, admin_id=admin.id, note=payload.note
    )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    order = order_service.get_order_or_404(db, order_id)
    order_service.delete_order(db, order)
