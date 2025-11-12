from pydantic import BaseModel
from typing import List, Optional


class GeminiAICreateImage(BaseModel):
    # item_images: List[UploadFile]
    # background_images: List[UploadFile]
    name: str
    description: Optional[str] = None
    background_description: Optional[str] = None
    price: float
    price_description: Optional[str] = None
    price_on_image: bool = False
    discount: Optional[int] = None
    discount_on_image: bool = False
    discount_description: Optional[str] = None
    aspect_ratio: str = "1:1"
