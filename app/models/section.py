from datetime import datetime

from sqlalchemy import String, DateTime, Table, Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

# A section can showcase one or several categories, and a category can
# appear in more than one section (e.g. "New In" and "Summer Picks" might
# both include the same category) -- hence a plain many-to-many table
# rather than a foreign key on either side.
section_categories = Table(
    "section_categories",
    Base.metadata,
    Column("section_id", Integer, ForeignKey("sections.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class Section(Base):
    """
    A curated homepage block the store owner can create, e.g. "Summer
    Collection" or "New Arrivals", pointing at one or more categories.
    The frontend fetches sections, then fetches products for each
    category the way it normally would (GET /api/products?category_id=..),
    so this table only needs to track title + which categories belong to it.
    """

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Controls display order on the homepage; lower = shown first.
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categories: Mapped[list["Category"]] = relationship(secondary=section_categories)
