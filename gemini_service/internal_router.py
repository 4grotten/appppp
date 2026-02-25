from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from settings import set_gemini_api_key, set_gemini_text_model, set_gemini_image_model

internal_router = APIRouter()

class APIKeyUpdate(BaseModel):
    api_key: str

class ModelUpdate(BaseModel):
    text_model: str = None
    image_model: str = None

@internal_router.post("/internal/update_api_key")
async def update_api_key_endpoint(data: APIKeyUpdate):
    if not data.api_key:
        raise HTTPException(status_code=400, detail="API Key is empty")
    set_gemini_api_key(data.api_key)
    return {"status": "success", "message": "API Key updated"}


@internal_router.post("/internal/update_models")
async def update_models_endpoint(data: ModelUpdate):
    if not data.text_model and not data.image_model:
        raise HTTPException(status_code=400, detail="At least one model must be provided")
    
    if data.text_model:
        set_gemini_text_model(data.text_model)
    
    if data.image_model:
        set_gemini_image_model(data.image_model)
    
    return {
        "status": "success",
        "message": "Models updated",
        "text_model": data.text_model,
        "image_model": data.image_model
    }
