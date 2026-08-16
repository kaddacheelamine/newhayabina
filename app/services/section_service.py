from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.section import Section


def _resolve_categories(db: Session, category_ids: list[int]) -> list[Category]:
    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    found_ids = {c.id for c in categories}
    missing = set(category_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category ids not found: {sorted(missing)}",
        )
    return categories


def list_sections(db: Session) -> list[Section]:
    return (
        db.query(Section)
        .options(joinedload(Section.categories))
        .order_by(Section.display_order, Section.id)
        .all()
    )


def get_section_or_404(db: Session, section_id: int) -> Section:
    section = (
        db.query(Section)
        .options(joinedload(Section.categories))
        .filter(Section.id == section_id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return section


def create_section(db: Session, title: str, category_ids: list[int], display_order: int = 0) -> Section:
    categories = _resolve_categories(db, category_ids)
    section = Section(title=title, display_order=display_order, categories=categories)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def update_section(
    db: Session,
    section: Section,
    title: str | None,
    category_ids: list[int] | None,
    display_order: int | None,
) -> Section:
    if title is not None:
        section.title = title
    if display_order is not None:
        section.display_order = display_order
    if category_ids is not None:
        section.categories = _resolve_categories(db, category_ids)
    db.commit()
    db.refresh(section)
    return section


def delete_section(db: Session, section: Section) -> None:
    db.delete(section)
    db.commit()
