from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.variant import ProductVariant
from app.models.variant_size import VariantSize


class InsufficientStockError(Exception):
    def __init__(self, variant_id: int, size: str, requested: int, available: int):
        self.variant_id = variant_id
        self.size = size
        self.requested = requested
        self.available = available
        super().__init__(
            f"Variant {variant_id} size {size}: requested {requested}, only {available} available"
        )


def get_variant_or_404(db: Session, variant_id: int) -> ProductVariant:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return variant


def get_variant_size_or_404(db: Session, variant_id: int, size: str) -> VariantSize:
    variant_size = (
        db.query(VariantSize)
        .filter(VariantSize.variant_id == variant_id, VariantSize.size == size)
        .first()
    )
    if not variant_size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Size '{size}' is not available for variant {variant_id}",
        )
    return variant_size


def check_availability(db: Session, variant_id: int, size: str, quantity: int) -> None:
    """Raise if there isn't enough quantity for this variant/size.
    Does NOT lock rows -- see note in order_service about concurrency."""
    variant_size = get_variant_size_or_404(db, variant_id, size)
    if variant_size.quantity < quantity:
        raise InsufficientStockError(variant_id, size, quantity, variant_size.quantity)


def deduct_stock(db: Session, variant_id: int, size: str, quantity: int) -> VariantSize:
    """Reduce a variant/size's quantity. Raises InsufficientStockError if not
    enough stock. Caller is responsible for committing the transaction."""
    variant_size = get_variant_size_or_404(db, variant_id, size)
    if variant_size.quantity < quantity:
        raise InsufficientStockError(variant_id, size, quantity, variant_size.quantity)
    variant_size.quantity -= quantity
    db.add(variant_size)
    return variant_size


def restore_stock(db: Session, variant_id: int, size: str, quantity: int) -> VariantSize:
    """Add quantity back to a variant/size (used on cancellation after confirmation)."""
    variant_size = get_variant_size_or_404(db, variant_id, size)
    variant_size.quantity += quantity
    db.add(variant_size)
    return variant_size
