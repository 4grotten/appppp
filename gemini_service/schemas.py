from pydantic import BaseModel
from typing import List, Optional


class GeminiAICreateImage(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    background_description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "KGS"
    price_with_discount: Optional[float] = None
    price_description: Optional[str] = None
    price_on_image: bool = False
    discount: Optional[int] = None
    discount_on_image: bool = False
    discount_description: Optional[str] = None
    aspect_ratio: str = "1:1"


class GeneratePromptScheme(BaseModel):
    text: Optional[str]
