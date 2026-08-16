from pydantic import BaseModel


class SiteInfoOut(BaseModel):
    title: str | None = None
    description: str | None = None
    banner_image_path: str | None = None

    model_config = {"from_attributes": True}
