from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.schemas.variant import VariantUpdate, VariantOut
from app.services import product_service, upload_service

router = APIRouter(prefix="/api/variants", tags=["variants"])


@router.put("/{variant_id}", response_model=VariantOut)
def update_variant(
    variant_id: int, payload: VariantUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    variant = product_service.get_variant_or_404(db, variant_id)
    return product_service.update_variant(db, variant, payload.name, payload.color, payload.sizes)


@router.put("/{variant_id}/image", response_model=VariantOut)
def set_variant_image(
    variant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """
    Sets (or replaces) this variant's single photo. A product's overall
    image gallery is just the collection of each of its variants' photo --
    there's no separate product-level image upload anymore.
    """
    variant = product_service.get_variant_or_404(db, variant_id)

    old_path = variant.image_path
    new_path = upload_service.save_product_image(file)
    variant.image_path = new_path
    db.commit()
    db.refresh(variant)

    if old_path:
        upload_service.delete_image_file(old_path)

    return variant


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(variant_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    variant = product_service.get_variant_or_404(db, variant_id)
    if variant.image_path:
        upload_service.delete_image_file(variant.image_path)
    db.delete(variant)
    db.commit()
