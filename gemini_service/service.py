import io
import traceback

import httpx
from fastapi import UploadFile
from fastapi.exceptions import HTTPException
from google.genai import Client, errors, types
from PIL import Image
from schemas import GeminiAICreateImage
from settings import (
    PRODUCTION,
    PROXY_HOST,
    PROXY_PASS,
    PROXY_PORT,
    PROXY_USER,
    get_gemini_api_key,
)


class GeminiAIService:
    _client = None

    PROMPT_TEMPLATES = {
        "item_description": (
            "Ты — копирайтер для маркетплейса. "
            "Твоя задача: Написать продающее, но лаконичное описание товара на основе входных данных. не ограничивайся строками пиши сколько хочешь"
            "подробно с использованием эмоджи и мотивацией для покупки"
        ),
        "prompt": (
            "Ты — профессиональный промпт-инженер для нейросетей (gemini imagen). "
            "Твоя задача: Составить детальный визуальный промпт для генерации изображения этого товара. "
            "Включи детали: стиль (фотореализм, 8k), освещение (кинематографичное), ракурс, фон. "
            "в одно предложение или абзац, без лишних вступлений."
        ),
        "price_prompt": (
            "Твоя задача: Описать стилистику текста для отображения ЦЕНЫ на фото.  на 3 строки без подробностей и мета описаний, не используй звездочки"
        ),
        "discount_prompt": (
            "Твоя задача: Описать стилистику текста для отображения СКИДКИ на фото.  на 3 строки без подробностей и мета описаний, не используй звездочки"
        ),
    }

    @classmethod
    def get_client(cls):
        api_key = get_gemini_api_key()

        if not api_key:
            print("WARNING: Gemini API key is empty!")
        else:
            # Mask API key for security (show first 8 and last 4 chars)
            print(f"[GEMINI] Using API key: {api_key}")

        if PRODUCTION:
            print(f"[GEMINI] PRODUCTION mode: direct connection (api_key={'set' if api_key else 'EMPTY'})")
            http_client = httpx.AsyncClient()
        else:
            proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
            print(f"[GEMINI] DEV mode: using proxy {proxy_url}")
            transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
            http_client = httpx.AsyncClient(transport=transport)

        return Client(
            api_key=api_key,
            http_options=types.HttpOptions(httpx_async_client=http_client),
        ).aio

    @classmethod
    async def check_proxy_ip(cls):
        if PRODUCTION:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://ipinfo.io/json")
                print(f"Direct IP: {resp.json()}")
        else:
            proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
            transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
            async with httpx.AsyncClient(transport=transport) as client:
                resp = await client.get("https://ipinfo.io/json")
                print(f"IP from proxy: {resp.json()}")

    @classmethod
    async def generate_from_prompt(
        cls, item_images, background_images, request: GeminiAICreateImage
    ):
        try:
            print("[GEMINI][generate_from_prompt] START")
            max_retries = 3
            images = list()
            background_images = background_images
            print(
                f"[GEMINI][generate_from_prompt] item_images={len(item_images) if item_images else 0}, "
                f"background_images={len(background_images) if background_images else 0}, "
                f"aspect_ratio={getattr(request, 'aspect_ratio', None)}"
            )

            images_prompt = []
            if background_images:
                images += background_images
            if item_images:
                images += item_images
            if images:
                for idx, file in enumerate(images, start=1):
                    try:
                        print(
                            f"[GEMINI][generate_from_prompt] reading image {idx}/{len(images)}: "
                            f"filename={getattr(file, 'filename', 'unknown')}"
                        )
                        image_bytes = await file.read()
                        print(
                            f"[GEMINI][generate_from_prompt] image {idx} bytes={len(image_bytes) if image_bytes else 0}"
                        )
                        image = Image.open(io.BytesIO(image_bytes))
                        if image.mode in ("RGBA", "LA", "P"):
                            image = image.convert("RGB")
                        images_prompt.append(image)
                    except Exception as image_error:
                        print(
                            f"[GEMINI][generate_from_prompt] image processing failed for "
                            f"{getattr(file, 'filename', 'unknown')}: {image_error}"
                        )
                        print(traceback.format_exc())
                        raise HTTPException(
                            status_code=400,
                            detail={"message": "error while trying to load a images"},
                        )

            name = request.name or "product"
            desc = request.description or None
            bg = request.background_description or ""
            price = request.price
            price_desc = request.price_description or ""
            discount = request.discount
            discount_desc_en = request.discount_description or ""
            aspect_ratio = request.aspect_ratio

            prompt_parts = [
                f"Create a professional, high-quality product image for '{name}'."
                f"Don't use description and name on the image, use it only if i say so"
            ]

            if bg:
                prompt_parts.append(f"Background should reflect: '{bg}'.")
            else:
                prompt_parts.append(f"Product description: '{desc}'.")
            if request.price_on_image and price:
                prompt_parts.append(
                    f"Show price: {price} with currency {request.currency}"
                )

                if price_desc:
                    prompt_parts.append(f" use prompt:'{price_desc}'")
                prompt_parts.append(" On the image.")

            if request.discount_on_image and discount:
                prompt_parts.append(f"Show discount: {discount}")

                if request.price_with_discount:
                    prompt_parts.append(
                        f"Show {request.price_with_discount} price it's price after discount use it like difference between prices"
                    )
                if discount_desc_en:
                    prompt_parts.append(f" use prompt: '{discount_desc_en}'")
                prompt_parts.append(" On the image.")

            if images_prompt:
                prompt_parts.append(
                    "Use the provided reference images to accurately render the product, "
                    "its shape, color, texture, and details. "
                    "Combine elements naturally. Do not hallucinate new objects."
                )

            contents = []
            contents.extend(prompt_parts)
            print(
                f"[GEMINI][generate_from_prompt] prompt_parts={len(prompt_parts)}, "
                f"images_prompt={len(images_prompt)}"
            )
            print(f"[GEMINI][generate_from_prompt] prompt preview: {' '.join(prompt_parts)[:700]}")

            if images_prompt:
                contents.extend(images_prompt)

                contents.append(
                    "Strictly base the generation on the provided images. "
                    "Maintain product accuracy. Output only the final image."
                )
            response = None
            for i in range(max_retries):
                try:
                    print(
                        f"[GEMINI][generate_from_prompt] request try={i + 1}/{max_retries}, "
                        f"contents_count={len(contents)}"
                    )
                    response = await cls.get_client().models.generate_content(
                        model="gemini-3-pro-image-preview",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                        ),
                    )
                    print(
                        f"[GEMINI][generate_from_prompt] response received, "
                        f"has_parts={bool(getattr(response, 'parts', None))}"
                    )
                    if response.parts:
                        print("[GEMINI][generate_from_prompt] response.parts present, breaking retry loop")
                        break
                    else:
                        print("[GEMINI][generate_from_prompt] response.parts is empty -> return None")
                        return None
                except errors.APIError as e:
                    if e.code == 503:
                        print(f"[GEMINI][generate_from_prompt] APIError 503 -> retry: {e.message}")
                    elif e.code == 429:
                        print(f"[GEMINI][generate_from_prompt] APIError 429 QUOTA EXCEEDED:")
                        print(f"  Message: {e.message}")
                        print(f"  Details: {e.details}")
                        return None
                    else:
                        print(f"[GEMINI][generate_from_prompt] Gemini API error: {e.code} \n\n{e.details}\n\n{e.message}")
                        return None

            image_bytes = None
            if response is None:
                print("[GEMINI][generate_from_prompt] response is None after retries")
                return None

            image_bytes = None
            if response is None:
                print("[GEMINI][generate_from_prompt] response is None after retries")
                return None

            for part in response.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    print(
                        f"[GEMINI][generate_from_prompt] inline image bytes={len(image_bytes) if image_bytes else 0}"
                    )

            if not image_bytes:
                print("[GEMINI][generate_from_prompt] no inline image data found in response.parts")
                raise HTTPException(
                    status_code=500, detail={"message": "failed to generate file"}
                )
            print("[GEMINI][generate_from_prompt] SUCCESS")
            return image_bytes

        except Exception as e:
            print(f"[GEMINI][generate_from_prompt] ERROR: {e}")
            print(traceback.format_exc())
            return None

    @classmethod
    async def generate_prompt(
        cls, desc_type: str, pivot: str, images: list[UploadFile]
    ):
        print("[GEMINI][generate_prompt] START")
        print(
            f"[GEMINI][generate_prompt] desc_type={desc_type}, "
            f"pivot_len={len(pivot) if isinstance(pivot, str) else 0}, "
            f"images_count={len(images) if isinstance(images, list) else 0}"
        )
        contents = []
        max_retries = 3
        system_instruction = cls.PROMPT_TEMPLATES.get(
            desc_type, cls.PROMPT_TEMPLATES["item_description"]
        )

        full_prompt_text = f"{system_instruction}\n\nДанные для обработки:\n"

        if isinstance(pivot, str):
            # Если пользователь ввел текст (например "хочу мрачную атмосферу")
            full_prompt_text += (
                f" так же используй язык текста, Текст пользователя: {pivot}"
            )
            contents.append(full_prompt_text)

        if isinstance(images, list):
            full_prompt_text += "Изображения товара (см. вложения)."
            contents.append(full_prompt_text)
            for idx, file in enumerate(images, start=1):
                try:
                    print(
                        f"[GEMINI][generate_prompt] reading image {idx}/{len(images)}: "
                        f"filename={getattr(file, 'filename', 'unknown')}"
                    )
                    image_bytes = await file.read()
                    image = Image.open(io.BytesIO(image_bytes))

                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")

                    contents.append(image)
                except Exception as image_error:
                    print(
                        f"[GEMINI][generate_prompt] skip image "
                        f"{getattr(file, 'filename', 'unknown')} due to: {image_error}"
                    )
                    print(traceback.format_exc())
                    continue

        contents.append(" Не используй markdown и не добавляй звездочек!")
        print(f"[GEMINI][generate_prompt] contents_count={len(contents)}")

        try:
            for retry in range(max_retries):
                try:
                    print(f"[GEMINI][generate_prompt] request try={retry + 1}/{max_retries}")
                    response = await cls.get_client().models.generate_content(
                        model="gemini-2.5-pro",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_modalities=["Text"],
                            temperature=0.7,
                        ),
                    )

                    print(
                        f"[GEMINI][generate_prompt] response_text_len="
                        f"{len(response.text) if getattr(response, 'text', None) else 0}"
                    )
                    return response.text.strip() if response.text else None
                except errors.APIError as e:
                    if e.code == 503:
                        print(f"[GEMINI][generate_prompt] APIError 503, retry={retry + 1}: {e.message}")
                    elif e.code == 429:
                        print(f"[GEMINI][generate_prompt] APIError 429 QUOTA EXCEEDED:")
                        print(f"  Message: {e.message}")
                        print(f"  Details: {e.details}")
                        print(f"  HINT: Check API key billing status at https://ai.google.dev/")
                        return None
                    else:
                        print(
                            f"[GEMINI][generate_prompt] APIError: code={e.code}, "
                            f"message={e.message}, details={e.details}"
                        )
                        return None

        except Exception as e:
            print(f"[GEMINI][generate_prompt] ERROR: {e}")
            print(traceback.format_exc())
            return None
