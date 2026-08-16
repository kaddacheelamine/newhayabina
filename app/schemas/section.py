from pydantic import BaseModel, Field

from app.schemas.category import CategoryOut


class SectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    category_ids: list[int] = Field(min_length=1, description="One or more category IDs to feature in this section.")
    display_order: int = 0


class SectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    category_ids: list[int] | None = Field(default=None, min_length=1)
    display_order: int | None = None


class SectionOut(BaseModel):
    id: int
    title: str
    display_order: int
    categories: list[CategoryOut] = []

    model_config = {"from_attributes": True}
