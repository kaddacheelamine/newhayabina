from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteInfo(Base):
    """
    Singleton table (always exactly one row, id=1) holding the site-wide
    branding shown by the frontend: title, description, and a banner/hero
    image. Kept as its own table rather than reusing the generic
    key/value `settings` table because it needs an actual uploaded image
    file, not just a text value.
    """

    __tablename__ = "site_info"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    banner_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
