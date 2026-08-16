from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Numeric, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from app.database import Base


class Product(Base):
    """
    NOTE ON STOCK AND IMAGES:
    Stock and images both live on variants now, not on Product directly.
    - `stock` sums every VariantSize.quantity across all of this
      product's variants -- one source of truth, no drift.
    - There is no separate product-level image list: a product's
      "gallery" is simply the collection of each of its variants' single
      image (see the `images` property below, which just gathers those).
    """

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "discount_percentage >= 0 AND discount_percentage <= 1",
            name="ck_products_discount_percentage_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    # Free-text material info (e.g. "Cotton", "Wool", "100% Polyester").
    # Kept as free text rather than a fixed enum since materials/blends are
    # too varied to enumerate meaningfully.
    material: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Which season the item is meant for. Nullable = not specified / all-season
    # items can also just use ALL_SEASON explicitly if you want it filterable.
    season: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # 0 = no discount, 1 = 100% off. Stored as a ratio (not a 0-100 percent)
    # so `price * (1 - discount_percentage)` is a direct final-price calculation
    # with no extra /100 step anywhere in the codebase.
    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0")
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    @hybrid_property
    def stock(self) -> int:
        return sum(size.quantity for variant in self.variants for size in variant.sizes)

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock <= 0

    @property
    def final_price(self) -> Decimal:
        """Price after discount is applied. Frontend should display this
        as the "real" price and can show `price` crossed-out when
        discount_percentage > 0."""
        return (self.price * (Decimal("1") - self.discount_percentage)).quantize(Decimal("0.01"))

    @property
    def colors(self) -> list[str]:
        """Convenience list of this product's distinct variant colors."""
        seen = []
        for v in self.variants:
            if v.color not in seen:
                seen.append(v.color)
        return seen

    @property
    def thumbnail(self) -> str | None:
        """First variant's image, for list views that just need one
        preview picture rather than the full gallery."""
        for v in self.variants:
            if v.image_path:
                return v.image_path
        return None
