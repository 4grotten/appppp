from google.genai import Client, types, errors
from fastapi.exceptions import HTTPException
from schemas import GeminiAICreateImage
from PIL import Image
import io
from settings import GEMINI_API_KEY, PROXY_PASS, PROXY_HOST, PROXY_PORT, PROXY_USER
import httpx
from fastapi import UploadFile


class GeminiAIService:
    _client = None
    GEMINI_PROXY = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    PROMPT_TEMPLATES = {
        # 1. Для поля "Описание товара" (обычный текст)
        "item_description": (
            "Ты — копирайтер для маркетплейса. "
            "Твоя задача: Написать продающее, но лаконичное описание товара на основе входных данных. "
            "Пиши на русском. Не используй маркеров (markdown), просто текст."
        ),
        
        # 2. Для поля "Промт для генерации" (то, что на скрине с фотореализмом)
        "prompt": (
            "Ты — профессиональный промпт-инженер для нейросетей (Stable Diffusion, Midjourney). "
            "Твоя задача: Составить детальный визуальный промпт для генерации изображения этого товара. "
            "Включи детали: стиль (фотореализм, 8k), освещение (кинематографичное), ракурс, фон (неоновые огни, улица и т.д., если подходит). "
            "Ответ должен быть на русском языке, в одно предложение или абзац, без лишних вступлений."
        ),
        
        # 3. Для поля "Цена" (стиль текста цены)
        "price_prompt": (
            "Твоя задача: Описать стилистику текста для отображения ЦЕНЫ на фото. "
            "Пользователь даст краткие пожелания (или фото), а ты преврати это в инструкцию для дизайнера. "
            "Например: 'Крупный жирный шрифт красного цвета в правом верхнем углу'. "
            "Ответ на русском, кратко."
        ),
        
        # 4. Для поля "Скидка" (стиль текста скидки)
        "discount_prompt": (
            "Твоя задача: Описать стилистику текста для отображения СКИДКИ на фото. "
            "Опиши цвет, расположение и стиль плашки или текста скидки на основе данных. "
            "Ответ на русском, кратко."
        )
    }

    @classmethod
    def get_client(cls):
        if cls._client is None:
            proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
            # proxy = httpx.Proxy(url=proxy_url)
            transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
            http_client = httpx.AsyncClient(transport=transport)
            cls._client = Client(
                api_key=GEMINI_API_KEY,
                http_options=types.HttpOptions(httpx_async_client=http_client),
            ).aio
        return cls._client

    @classmethod
    async def generate_from_prompt(
        cls, item_images, background_images, request: GeminiAICreateImage
    ):
        try:
            max_retries = 3
            item_images = item_images
            background_images = background_images

            images_prompt = []
            if item_images:
                if background_images:
                    item_images += background_images
                for file in item_images:
                    try:
                        image_bytes = await file.read()
                        image = Image.open(io.BytesIO(image_bytes))
                        if image.mode in ("RGBA", "LA", "P"):
                            image = image.convert("RGB")
                        images_prompt.append(image)
                    except Exception as e:
                        raise HTTPException(
                            status_code=400,
                            detail={"message": "error while trying to load a images"},
                        )

            name = request.name or "product"
            desc = request.description or ""
            bg = request.background_description or ""
            price = request.price
            price_desc = request.price_description or ""
            discount = request.discount
            discount_desc_en = request.discount_description or ""
            aspect_ratio = request.aspect_ratio

            prompt_parts = [
                f"Create a professional, high-quality product image for '{name}'."
                f"Product description: '{desc}'."
                f"Don't use description and name on the image, use it only if i say so"
            ]

            if bg:
                prompt_parts.append(f"Background should reflect: '{bg}'.")

            if request.price_on_image and price:
                prompt_parts.append(f"Show price: {price}")

                if price_desc:
                    prompt_parts.append(f" use properties:'{price_desc}'")
                prompt_parts.append(" On the image.")

            if request.discount_on_image and discount:
                prompt_parts.append(f"Show discount: {discount}")
                if discount_desc_en:
                    prompt_parts.append(f" use properties: '{discount_desc_en}'")
                prompt_parts.append(" On the image.")

            if images_prompt:
                prompt_parts.append(
                    "Use the provided reference images to accurately render the product, "
                    "its shape, color, texture, and details. "
                    "If background images are provided, use them as inspiration or direct background. "
                    "Combine elements naturally. Do not hallucinate new objects."
                )

            contents = []
            contents.extend(prompt_parts)

            if images_prompt:
                contents.extend(images_prompt)

                contents.append(
                    "Strictly base the generation on the provided images. "
                    "Maintain product accuracy. Output only the final image."
                )
            for i in range(max_retries):
                try:
                    response = await cls.get_client().models.generate_content(
                        model="gemini-2.5-flash-image",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                        ),
                    )
                    if response.parts:
                        break
                    else:
                        return None
                except errors.APIError as e:
                    if e.code == 503:
                        print(f"Error gemini return 503 -> retry {e.message}")
                    else:
                        return None

            for part in response.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data

            if not image_bytes:
                raise HTTPException(
                    status_code=500, detail={"message": "failed to generate file"}
                )
            return image_bytes

        except Exception as e:
            print(f"Gemini error: {e}")
            return None

    @classmethod
    async def generate_prompt(cls, desc_type: str, pivot:str, images: list[UploadFile]):
        contents = []
        max_retries = 3
        system_instruction = cls.PROMPT_TEMPLATES.get(desc_type, cls.PROMPT_TEMPLATES["item_description"])

        full_prompt_text = f"{system_instruction}\n\nДанные для обработки:\n"

        if isinstance(pivot, str):
                    # Если пользователь ввел текст (например "хочу мрачную атмосферу")
                    full_prompt_text += f"Не добавляй мета слова только то что я попросил, Текст пользователя: {pivot}"
                    contents.append(full_prompt_text)
                
        if isinstance(images, list):
            # Если пользователь загрузил картинки
            full_prompt_text += "Не добавляй мета слова только то что я попросил, Изображения товара (см. вложения)."
            contents.append(full_prompt_text)
            print(f"Эта часть сработала!")
            for file in images:
                try:
                    # Считываем картинку
                    # Важно: file.seek(0) может понадобиться, если файл уже читали
                    image_bytes = await file.read()
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")
                        
                    contents.append(image)
                except Exception:
                    continue

        try:
            for retry in range(max_retries):
                try:
                    response = await cls.get_client().models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_modalities=["Text"],
                            temperature=0.7, 
                        ),
                    )
                    
                    # Возвращаем чистый текст
                    return response.text.strip() if response.text else None
                except errors.APIError as e:
                    if e.code == 503:
                        print(f"The model is overloaded trying again {retry}")

        except Exception as e:
            # Тут лучше добавить логгер
            print(f"Gemini Error: {e}")
            return None
