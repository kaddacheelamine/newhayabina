from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ProductVariant(Base):
    """
    A variant is now the actual sellable unit that carries its own name,
    color, and single photo -- a "Red" version and a "Green" version of
    the same product are two separate variants, even though they share
    the parent Product's name/price/description. A variant can be
    available in several sizes (see VariantSize), each with its own
    stock quantity.
    """

    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    # Unique across the whole store (not just within this product) --
    # matches "the variant name never repeats." If you actually want
    # uniqueness scoped per-product instead (e.g. two different products
    # both having a variant literally named "Red"), say so and this is a
    # one-line change (move the constraint to a composite
    # UniqueConstraint("product_id", "name")).
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    color: Mapped[str] = mapped_column(String(64), nullable=False)

    # Exactly one image per variant. All of a product's variant images
    # together ARE the product's image gallery -- there's no separate
    # per-product image list anymore.
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(back_populates="variants")
    sizes: Mapped[list["VariantSize"]] = relationship(
        back_populates="variant", cascade="all, delete-orphan"
    )

    @property
    def total_quantity(self) -> int:
        return sum(s.quantity for s in self.sizes)

    @property
    def is_out_of_stock(self) -> bool:
        return self.total_quantity <= 0
