from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone1: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    phone2: Mapped[str | None] = mapped_column(String(32), nullable=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
