from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    phone1: str = Field(min_length=6, max_length=32)
    phone2: str | None = Field(default=None, max_length=32)


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int

    model_config = {"from_attributes": True}
