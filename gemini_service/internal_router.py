from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from settings import set_gemini_api_key

internal_router = APIRouter()

class APIKeyUpdate(BaseModel):
    api_key: str

@internal_router.post("/internal/update_api_key")
async def update_api_key_endpoint(data: APIKeyUpdate):
    if not data.api_key:
        raise HTTPException(status_code=400, detail="API Key is empty")
    set_gemini_api_key(data.api_key)
    return {"status": "success", "message": "API Key updated"}