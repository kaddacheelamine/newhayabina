from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate
from app.services import stock_service

# Terminal states that no longer accept a transition.
_TERMINAL_STATES = {OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value}

# Valid forward transitions. Kept simple and explicit rather than allowing
# any-status-to-any-status jumps.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING.value: {OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value},
    OrderStatus.CONFIRMED.value: {OrderStatus.PREPARING.value, OrderStatus.CANCELLED.value},
    OrderStatus.PREPARING.value: {OrderStatus.SHIPPING.value, OrderStatus.CANCELLED.value},
    OrderStatus.SHIPPING.value: {OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value},
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}

_ITEM_LOAD_OPTIONS = (
    joinedload(Order.items).joinedload(OrderItem.product),
    joinedload(Order.items).joinedload(OrderItem.variant),
)


def get_order_or_404(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(joinedload(Order.customer), *_ITEM_LOAD_OPTIONS)
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def create_order(db: Session, payload: OrderCreate) -> Order:
    """
    Places a new order as PENDING. Stock is only *validated* here (so we can
    reject obviously-impossible orders immediately), not deducted -- deduction
    happens on confirmation. This matches the spec: don't touch inventory
    until an admin confirms.

    NOTE ON CONCURRENCY: SQLite doesn't support row-level locking (SELECT ...
    FOR UPDATE), so this availability check has a theoretical race window
    between two simultaneous orders for the last unit of a variant/size.
    That's fine for a single-admin storefront processing confirmations
    manually (the real deduction + final check happens at confirm_order,
    which will reject the second one atomically). If this ever moves to
    Postgres/MySQL under real concurrent load, add SELECT FOR UPDATE in
    confirm_order.
    """
    customer = Customer(
        first_name=payload.customer.first_name,
        last_name=payload.customer.last_name,
        phone1=payload.customer.phone1,
        phone2=payload.customer.phone2,
    )
    db.add(customer)
    db.flush()  # get customer.id without committing

    order = Order(
        customer_id=customer.id,
        delivery_type=payload.delivery_type.value,
        wilaya=payload.wilaya,
        commune=payload.commune,
        address=payload.address,
        status=OrderStatus.PENDING.value,
        total=Decimal("0"),
    )
    db.add(order)
    db.flush()

    total = Decimal("0")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
        if not variant or variant.product_id != product.id:
            raise HTTPException(
                status_code=404,
                detail=f"Variant {item.variant_id} not found for product {item.product_id}",
            )

        # Soft check only -- see note above. Doesn't reserve stock. Also
        # 404s here if the size doesn't exist at all for this variant.
        variant_size = stock_service.get_variant_size_or_404(db, variant.id, item.size)
        if variant_size.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Not enough stock for {product.name} - {variant.name} "
                    f"({variant.color}, size {item.size}): {variant_size.quantity} available"
                ),
            )

        unit_price = product.price
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            variant_id=variant.id,
            size=item.size,
            quantity=item.quantity,
            price=unit_price,
        )
        db.add(order_item)
        total += unit_price * item.quantity

    order.total = total
    db.add(
        OrderStatusHistory(order_id=order.id, from_status=None, to_status=OrderStatus.PENDING.value)
    )

    db.commit()
    db.refresh(order)
    return order


def _validate_transition(current: str, target: str) -> None:
    if current in _TERMINAL_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order is already {current} and cannot be changed",
        )
    if target not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot move order from {current} to {target}",
        )


def update_order_status(
    db: Session,
    order: Order,
    new_status: str,
    admin_id: int | None,
    note: str | None = None,
) -> Order:
    """
    Central place where status transitions happen. This is where stock is
    actually deducted (on the transition INTO CONFIRMED) and restored (on
    CANCELLED, if it had already been deducted). Every transition is logged
    to order_status_history for auditability.
    """
    current = order.status
    _validate_transition(current, new_status)

    if new_status == OrderStatus.CONFIRMED.value and not order.stock_deducted:
        # This is the one moment stock actually leaves inventory.
        for item in order.items:
            try:
                stock_service.deduct_stock(db, item.variant_id, item.size, item.quantity)
            except stock_service.InsufficientStockError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Cannot confirm order: insufficient stock for variant "
                        f"{exc.variant_id} size {exc.size} "
                        f"(requested {exc.requested}, available {exc.available})"
                    ),
                ) from exc
        order.stock_deducted = True

    if new_status == OrderStatus.CANCELLED.value and order.stock_deducted:
        # Order had already consumed inventory (was CONFIRMED or later) --
        # give it back.
        for item in order.items:
            stock_service.restore_stock(db, item.variant_id, item.size, item.quantity)
        order.stock_deducted = False

    order.status = new_status
    db.add(order)
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=current,
            to_status=new_status,
            changed_by_admin_id=admin_id,
            note=note,
        )
    )
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, status_filter: str | None = None) -> list[Order]:
    query = db.query(Order).options(joinedload(Order.customer), *_ITEM_LOAD_OPTIONS)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    return query.order_by(Order.created_at.desc()).all()


def delete_order(db: Session, order: Order) -> None:
    """Deleting an order that already deducted stock restores it first,
    so inventory never silently disappears."""
    if order.stock_deducted:
        for item in order.items:
            stock_service.restore_stock(db, item.variant_id, item.size, item.quantity)
    db.delete(order)
    db.commit()
