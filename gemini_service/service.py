from google.genai import Client, types
from fastapi.exceptions import HTTPException
from schemas import GeminiAICreateImage
from PIL import Image
import io
from settings import GEMINI_API_KEY, PROXY_PASS, PROXY_HOST, PROXY_PORT, PROXY_USER
import httpx


class GeminiAIService:
    _client = None
    GEMINI_PROXY = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

    @classmethod
    def get_client(cls):
        if cls._client is None:
            proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
            # proxy = httpx.Proxy(url=proxy_url)
            transport = httpx.HTTPTransport(proxy=proxy_url)
            http_client = httpx.Client(transport=transport)
            cls._client = Client(
                api_key=GEMINI_API_KEY,
                http_options=types.HttpOptions(httpx_client=http_client),
            )
        return cls._client

    @classmethod
    async def generate_from_prompt(
        cls, item_images, background_images, request: GeminiAICreateImage
    ):
        try:
            item_images = item_images
            background_images = background_images
            final_prompt = []
            data = {}

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
            description = request.description or ""
            background_description = request.background_description
            price = request.price
            discount = request.discount
            aspect_ratio = request.aspect_ratio

            prompt_parts = [
                f"Create a professional, high-quality product image for '{name}'."
                f"Product description: '{description}'."
            ]

            if background_description:
                prompt_parts.append(
                    f"Background should reflect: '{background_description}'."
                )

            if request.price_on_image and price:
                prompt_parts.append(f"Show price: {price}")

                if request.price_description:
                    prompt_parts.append(
                        f" that have those properties:'{request.price_description}'"
                    )
                prompt_parts.append(" On the image.")

            if request.discount_on_image and discount:
                prompt_parts.append(f"Show discount: {discount}")
                if request.discount_description:
                    prompt_parts.append(
                        f" that have those properties: '{request.discount_description}'"
                    )
                prompt_parts.append(" On the image.")

            if images_prompt:
                prompt_parts.append(
                    "Use the provided reference images to accurately render the product, "
                    "its shape, color, texture, and details. "
                    "If background images are provided, use them as inspiration or direct background. "
                    "Combine elements naturally. Do not hallucinate new objects."
                )

            contents = []
            contents.extend(images_prompt)

            if images_prompt:
                contents.extend(images_prompt)

                contents.append(
                    "Strictly base the generation on the provided images. "
                    "Maintain product accuracy. Output only the final image."
                )

            response = cls.get_client().models.generate_content(
                model="gemini-2.5-flash-image",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["Image"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )

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
