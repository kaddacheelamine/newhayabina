from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VariantSize(Base):
    """One size option within a variant, with its own stock quantity.
    E.g. variant "Red Wool Sweater" might have rows (S, qty=5), (M, qty=8) --
    sizes and their quantities can differ freely from one variant to
    another, which is expected and normal."""

    __tablename__ = "variant_sizes"
    __table_args__ = (
        UniqueConstraint("variant_id", "size", name="uq_variant_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), nullable=False)
    size: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    variant: Mapped["ProductVariant"] = relationship(back_populates="sizes")

    @property
    def is_out_of_stock(self) -> bool:
        return self.quantity <= 0
