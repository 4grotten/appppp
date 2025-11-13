from google.genai import Client, types
from fastapi.exceptions import HTTPException
from schemas import GeminiAICreateImage
from PIL import Image
import io
import os
from settings import GEMINI_API_KEY, PROXY_PASS, PROXY_HOST, PROXY_PORT, PROXY_USER
import httpx


class GeminiAIService:
    _client = None
    GEMINI_PROXY = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

    @classmethod
    def get_client(cls):
        if cls._client is None:
            proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
            proxy = httpx.Proxy(url=proxy_url)
            transport = httpx.Client(proxies=proxy)
            cls._client = Client(
                api_key=GEMINI_API_KEY,
                http_options=types.HttpOptions(httpx_client=transport),
            )
        return cls._client

    @classmethod
    async def generate_from_prompt(
        cls, item_images, background_images, request: GeminiAICreateImage
    ):
        old_http = os.environ.get("HTTP_PROXY")
        old_https = os.environ.get("HTTPS_PROXY")

        os.environ["HTTP_PROXY"] = cls.GEMINI_PROXY
        os.environ["HTTPS_PROXY"] = cls.GEMINI_PROXY
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
                        images_prompt.append(image)
                    except Exception as e:
                        raise HTTPException(
                            status_code=400,
                            detail={"message": "error while trying to load a images"},
                        )

            name = request.name
            description = request.description
            background_description = request.background_description
            price = request.price
            price_on_image = request.price_on_image
            price_description = request.price_description
            discount = request.discount
            discount_on_image = request.discount_on_image
            discount_description = request.discount_description
            aspect_ratio = request.aspect_ratio

            prompt = f"Make a cool image for {name} for context there is an description '{description}'"
            if price_on_image:
                prompt += f" add a price to image price: {price}"
                if price_description:
                    prompt += f" that '{price_description}'"
            if discount_on_image:
                prompt += f" also add a discoint {discount} to image"
                if discount_description:
                    prompt += f" that '{discount_description}'"

            if background_description:
                prompt += (
                    f" add to background those properties '{background_description}'"
                )

            final_prompt.append(prompt)
            if images_prompt:
                prompt += " and use images on prompt to generate background and objects if its"
                final_prompt.append(images_prompt)
            response = cls.get_client().models.generate_content(
                model="gemini-2.5-flash-image",
                contents=final_prompt,
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
        finally:
            if old_http is not None:
                os.environ["HTTP_PROXY"] = old_http
            else:
                os.environ.pop("HTTP_PROXY", None)
            if old_https is not None:
                os.environ["HTTPS_PROXY"] = old_https
            else:
                os.environ.pop("HTTPS_PROXY", None)
