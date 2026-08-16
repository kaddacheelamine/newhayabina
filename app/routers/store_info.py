from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.schemas.site_info import SiteInfoOut
from app.services import site_info_service, upload_service

router = APIRouter(prefix="/api/store-info", tags=["store-info"])


@router.get("", response_model=SiteInfoOut)
def get_store_info(db: Session = Depends(get_db)):
    """Public -- the frontend calls this to get the site title, description,
    and banner/hero image path to display on the homepage."""
    return site_info_service.get_site_info(db)


@router.put("", response_model=SiteInfoOut)
def update_store_info(
    title: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """
    Admin only. Multipart form so the banner image can be updated in the
    same request as the text -- send whichever fields you're changing,
    the rest are left as-is. Example (curl):

        curl -X PUT .../api/store-info \\
          -H "Authorization: Bearer $TOKEN" \\
          -F "title=My Store" \\
          -F "description=Best pajamas in town" \\
          -F "image=@banner.jpg"
    """
    info = site_info_service.get_site_info(db)

    if title is not None:
        info.title = title
    if description is not None:
        info.description = description
    if image is not None:
        info.banner_image_path = upload_service.save_banner_image(image)

    db.commit()
    db.refresh(info)
    return info
