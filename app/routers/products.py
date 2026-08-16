from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.schemas.variant import VariantCreate, VariantUpdate, VariantOut
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    category_id: int | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return product_service.list_products(db, category_id=category_id, search=search, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product_or_404(db, product_id)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    product = product_service.get_product_or_404(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    product = product_service.get_product_or_404(db, product_id)
    db.delete(product)
    db.commit()


# --- Variant creation lives here (nested under product); update/delete
# for an existing variant live in routers/variants.py at the top-level
# /api/variants/{id} path, matching the spec. ---

@router.post("/{product_id}/variants", response_model=VariantOut, status_code=status.HTTP_201_CREATED)
def add_variant(
    product_id: int, payload: VariantCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    return product_service.create_variant(db, product_id, payload.name, payload.color, payload.sizes)
