from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, Response
from schemas import GeminiAICreateImage
from service import GeminiAIService
from typing import List
import json


app = FastAPI()


@app.post("/api/v2/gemini/generate/image")
async def generate_image(
    # Файлы
    item_images: List[UploadFile] = File(None),
    background_images: List[UploadFile] = File(None),
    # Все остальные поля, принятые как Form
    name: str = Form(...),
    description: str = Form(None),
    background_description: str = Form(None),
    price: float = Form(...),
    price_description: str = Form(None),
    # FastAPI умеет преобразовывать "True"/"False" из формы в bool:
    price_on_image: bool = Form(None),
    discount: int = Form(None),
    discount_on_image: bool = Form(None),
    discount_description: str = Form(None),  # Используем None, если может быть пустым
    aspect_ratio: str = Form(...),
):
    try:
        # Создаем Pydantic объект для валидации и структурирования
        request_data = GeminiAICreateImage(
            name=name,
            description=description,
            background_description=background_description,
            price=price,
            price_description=price_description,
            price_on_image=price_on_image,
            discount=discount,
            discount_on_image=discount_on_image,
            discount_description=discount_description,
            aspect_ratio=aspect_ratio,
        )
    except Exception as e:
        return JSONResponse(
            {"detail": "invalid json format for data field or pydantic validation"},
            status_code=422,
        )

    response = await GeminiAIService.generate_from_prompt(
        item_images, background_images, request_data
    )

    return Response(
        content=response,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f"attachment; filename={request_data.name.replace(' ', '_')}.jpg"
        },
    )
