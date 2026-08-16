from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"), nullable=False)

    # Which size of the variant was ordered. A variant can offer several
    # sizes (see VariantSize) -- the customer picks one at checkout, same
    # as they'd pick a size on any real store.
    size: Mapped[str] = mapped_column(String(32), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # unit price at time of order

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant"] = relationship()

    @property
    def product_name(self) -> str:
        return self.product.name

    @property
    def variant_name(self) -> str:
        return self.variant.name
