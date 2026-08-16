from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import DeliveryType, OrderStatus
from app.schemas.customer import CustomerBase, CustomerOut


class OrderItemCreate(BaseModel):
    product_id: int
    variant_id: int
    size: str = Field(min_length=1, max_length=32)
    quantity: int = Field(ge=1)


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    variant_id: int
    variant_name: str
    size: str
    quantity: int
    price: Decimal

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    """Public payload used by customers placing an order."""

    customer: CustomerBase
    delivery_type: DeliveryType
    wilaya: str = Field(min_length=1, max_length=128)
    commune: str = Field(min_length=1, max_length=128)
    address: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderOut(BaseModel):
    id: int
    customer: CustomerOut
    delivery_type: str
    wilaya: str
    commune: str
    address: str | None
    total: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []

    model_config = {"from_attributes": True}
