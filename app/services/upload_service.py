import os
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _validate_image(file: UploadFile, raw_bytes: bytes) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
        )


def save_image(file: UploadFile, subdir: str) -> str:
    """Saves an uploaded image to uploads/<subdir>/ and returns the relative
    path stored in the DB (e.g. 'banners/<uuid>.jpg')."""
    raw_bytes = file.file.read()
    _validate_image(file, raw_bytes)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    target_dir = os.path.join(settings.upload_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)
    full_path = os.path.join(target_dir, filename)

    with open(full_path, "wb") as f:
        f.write(raw_bytes)

    # Re-encode through Pillow to strip metadata / verify it's a real image.
    try:
        with Image.open(full_path) as img:
            img.verify()
    except Exception as exc:
        os.remove(full_path)
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    return f"{subdir}/{filename}"


def save_product_image(file: UploadFile) -> str:
    """Saves an uploaded image to uploads/products/. Thin wrapper kept for
    backwards compatibility with existing callers."""
    return save_image(file, "products")


def save_banner_image(file: UploadFile) -> str:
    """Saves an uploaded image to uploads/banners/ (used for site-wide
    branding, e.g. the homepage hero image)."""
    return save_image(file, "banners")


def delete_image_file(relative_path: str) -> None:
    full_path = os.path.join(settings.upload_dir, relative_path)
    if os.path.exists(full_path):
        os.remove(full_path)


# Kept as an alias -- existing callers use this name.
delete_product_image_file = delete_image_file
