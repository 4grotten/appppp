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
    async def generate_prompt(cls, desc_type: str, pivot: list[UploadFile] | str):
        images = []
        if isinstance(pivot, list):
            base_prompt = "Using this image generate an"
            for file in pivot:
                try:
                    image_bytes = await file.read()
                    image = Image.open(io.BytesIO(image_bytes))
                    if image.mode in ("RGBA", "LA", "P"):
                        image = image.convert("RGB")
                    images.append(image)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail={"message": "error while trying to load a images"},
                    )
        else:
            base_prompt = f"Using this description {pivot} generate an"

        if desc_type == "item_description":
            prompt = " proffesional description which will be used to generate image and descripts image"
        else:
            prompt = f" proffesional {desc_type} description which will be used to generate image for gemini-2.5-flash-image"

        full_text_prompt = (
            base_prompt
            + prompt
            + " make text shorter don't use markdown and generate it on 'RU' language"
            + " don't add meta information send me only what i've asked"
        )

        final_prompt = [full_text_prompt]

        if images:
            final_prompt.extend(images)

        response = await cls.get_client().models.generate_content(
            model="gemini-2.5-pro",
            contents=final_prompt,
            config=types.GenerateContentConfig(response_modalities=["Text"]),
        )

        if response.text:
            return response.text
        else:
            return None
