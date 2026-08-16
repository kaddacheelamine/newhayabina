from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies import get_current_admin
from app.services import upload_service

router = APIRouter(prefix="/api", tags=["uploads"])


@router.post("/upload")
def upload_generic_image(file: UploadFile = File(...), _=Depends(get_current_admin)):
    """Generic upload -- saves the file and returns its path only, no DB
    row created. For product photos, prefer
    PUT /api/variants/{variant_id}/image instead (see routers/variants.py) --
    every product image belongs to a specific variant now, there's no
    standalone product-level image upload."""
    path = upload_service.save_product_image(file)
    return {"path": path}
