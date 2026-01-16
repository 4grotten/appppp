import logging
import os
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from schemas import GeminiAICreateImage
from service import GeminiAIService
from settings import set_gemini_api_key
from internal_router import internal_router 

app = FastAPI(
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json",
)
allowed_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v2/gemini/generate/image")
async def generate_image(
    # Файлы
    item_images: List[UploadFile] = File(None),
    background_images: List[UploadFile] = File(None),
    # Все остальные поля, принятые как Form
    name: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    background_description: Optional[str] = Form(default=None),
    price: Optional[float] = Form(default=None),
    currency: Optional[str] = Form(default=None),
    price_with_discount: Optional[float] = Form(default=None),
    price_description: Optional[str] = Form(default=None),
    # FastAPI умеет преобразовывать "True"/"False" из формы в bool:
    price_on_image: bool = Form(default=False),
    discount: Optional[int] = Form(default=None),
    discount_on_image: bool = Form(default=False),
    discount_description: Optional[str] = Form(default=None),
    aspect_ratio: str = Form(...),
):
    try:
        # Создаем Pydantic объект для валидации и структурирования
        request_data = GeminiAICreateImage(
            name=name,
            description=description,
            background_description=background_description,
            price=price,
            currency=currency,
            price_with_discount=price_with_discount,
            price_description=price_description,
            price_on_image=price_on_image,
            discount=discount,
            discount_on_image=discount_on_image,
            discount_description=discount_description,
            aspect_ratio=aspect_ratio,
        )
    except Exception:
        return JSONResponse(
            {"detail": "invalid json format for data field or pydantic validation"},
            status_code=422,
        )

    response = await GeminiAIService.generate_from_prompt(
        item_images, background_images, request_data
    )

    if not response:
        return JSONResponse(
            status_code=400, content={"message": "something went wrong"}
        )

    return Response(
        content=response,
        media_type="image/jpeg",
        headers={"Content-Disposition": "image.png"},
    )


@app.post("/api/v2/gemini/generate/prompt")
async def generate_prompt(
    desc_type: str,
    text: Optional[str] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
):
    data = dict()
    data["pivot"] = text if text else None
    data["images"] = images if images else None
    response = await GeminiAIService.generate_prompt(desc_type, **data)

    if response:
        return JSONResponse(content={"prompt": response}, status_code=200)
    else:
        return JSONResponse(content=None, status_code=400)

app.include_router(internal_router)

# class UpdateApiKeyPayload(BaseModel):
#     api_key: str


# @app.post("/internal/update_api_key")
# async def update_api_key(payload: UpdateApiKeyPayload):
#     logger = logging.getLogger(__name__)
#     try:
#         path = GEMINI_API_KEY_FILE
#         logger.info("Received request to update Gemini API key, writing to %s", path)
#         os.makedirs(os.path.dirname(path), exist_ok=True)
#         with open(path, "w") as f:
#             f.write(payload.api_key or "")
#         logger.info("Gemini API key written to %s", path)
#         return JSONResponse(status_code=200, content={"status": "ok"})
#     except Exception as e:
#         logger.exception("Failed to write Gemini API key to %s: %s", GEMINI_API_KEY_FILE, e)
#         raise HTTPException(status_code=500, detail=str(e))
