from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from schemas import GeminiAICreateImage, GeneratePromptScheme
from service import GeminiAIService
from typing import List, Optional

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
    name: str = Form(...),
    description: str = Form(None),
    background_description: str = Form(None),
    price: float = Form(None),
    currency: str = Form(None),
    price_with_discount: float = Form(None),
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
            currency=currency,
            price_with_discount=price_with_discount,
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
