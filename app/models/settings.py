from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteSetting(Base):
    """Simple key/value store for site-wide configuration
    (e.g. shipping fees, store name, contact info)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(1024), nullable=False)
