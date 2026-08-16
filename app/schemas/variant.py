from pydantic import BaseModel, Field


class VariantSizeIn(BaseModel):
    size: str = Field(min_length=1, max_length=32)
    quantity: int = Field(ge=0)


class VariantSizeOut(BaseModel):
    id: int
    size: str
    quantity: int
    is_out_of_stock: bool

    model_config = {"from_attributes": True}


class VariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Unique variant name, store-wide.")
    color: str = Field(min_length=1, max_length=64)
    sizes: list[VariantSizeIn] = Field(min_length=1, description="At least one size with its stock quantity.")


class VariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, min_length=1, max_length=64)
    sizes: list[VariantSizeIn] | None = Field(
        default=None,
        min_length=1,
        description="If provided, REPLACES the entire size list (not a merge/patch).",
    )


class VariantOut(BaseModel):
    id: int
    product_id: int
    name: str
    color: str
    image_path: str | None = None
    sizes: list[VariantSizeOut] = []
    total_quantity: int
    is_out_of_stock: bool

    model_config = {"from_attributes": True}
