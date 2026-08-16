from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_admin
from app.schemas.section import SectionCreate, SectionUpdate, SectionOut
from app.services import section_service

router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.get("", response_model=list[SectionOut])
def list_sections(db: Session = Depends(get_db)):
    """Public -- the frontend uses this to render homepage product
    sections (e.g. "Summer Collection"). Each section lists which
    categories it features; fetch products for those categories via the
    existing GET /api/products?category_id=... ."""
    return section_service.list_sections(db)


@router.get("/{section_id}", response_model=SectionOut)
def get_section(section_id: int, db: Session = Depends(get_db)):
    return section_service.get_section_or_404(db, section_id)


@router.post("", response_model=SectionOut, status_code=status.HTTP_201_CREATED)
def create_section(payload: SectionCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return section_service.create_section(db, payload.title, payload.category_ids, payload.display_order)


@router.put("/{section_id}", response_model=SectionOut)
def update_section(
    section_id: int, payload: SectionUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)
):
    section = section_service.get_section_or_404(db, section_id)
    return section_service.update_section(
        db, section, payload.title, payload.category_ids, payload.display_order
    )


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(section_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    section = section_service.get_section_or_404(db, section_id)
    section_service.delete_section(db, section)
