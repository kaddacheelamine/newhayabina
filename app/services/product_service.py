from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.variant_size import VariantSize
from app.schemas.variant import VariantSizeIn


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = (
        db.query(Product)
        .options(
            joinedload(Product.variants).joinedload(ProductVariant.sizes),
            joinedload(Product.category),
        )
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def list_products(
    db: Session,
    category_id: int | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Product]:
    query = db.query(Product).options(
        joinedload(Product.variants).joinedload(ProductVariant.sizes)
    )
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


def _check_name_unique(db: Session, name: str, exclude_variant_id: int | None = None) -> None:
    query = db.query(ProductVariant).filter(func.lower(ProductVariant.name) == name.lower())
    if exclude_variant_id is not None:
        query = query.filter(ProductVariant.id != exclude_variant_id)
    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A variant named '{name}' already exists -- variant names must be unique.",
        )


def create_variant(
    db: Session, product_id: int, name: str, color: str, sizes: list[VariantSizeIn]
) -> ProductVariant:
    get_product_or_404(db, product_id)
    _check_name_unique(db, name)

    variant = ProductVariant(product_id=product_id, name=name, color=color)
    variant.sizes = [VariantSize(size=s.size, quantity=s.quantity) for s in sizes]
    db.add(variant)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant name already exists") from exc
    db.refresh(variant)
    return variant


def update_variant(
    db: Session,
    variant: ProductVariant,
    name: str | None,
    color: str | None,
    sizes: list[VariantSizeIn] | None,
) -> ProductVariant:
    if name is not None and name != variant.name:
        _check_name_unique(db, name, exclude_variant_id=variant.id)
        variant.name = name
    if color is not None:
        variant.color = color
    if sizes is not None:
        # Replace-all semantics: simplest to reason about, avoids partial
        # merge ambiguity (e.g. what happens to a size omitted from the
        # payload?). Send the full desired size list every time.
        variant.sizes = [VariantSize(size=s.size, quantity=s.quantity) for s in sizes]

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Variant name already exists") from exc
    db.refresh(variant)
    return variant


def get_variant_or_404(db: Session, variant_id: int) -> ProductVariant:
    variant = (
        db.query(ProductVariant)
        .options(joinedload(ProductVariant.sizes))
        .filter(ProductVariant.id == variant_id)
        .first()
    )
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    return variant
