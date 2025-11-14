import httpx
import urllib


def _is_likely_english(text: str) -> bool:

    if len(text) < 3:
        return True

    latin_charts = sum(1 for c in text if c.isascii() or c.isalpha())

    if latin_charts / len(text) > 0.7:
        return True

    if any(ord(c) > 127 for c in text):
        return False

    return True


async def translate_to_english(text: str) -> str:
    if not text or not text.strip():
        return ""

    text = text.strip()

    if _is_likely_english(text):
        return text

    try:
        url = "https://translate.googleapis.com/translate_a/single"

        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": "en",
            "dt": "t",
            "q": text[:5000],
        }

        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            translated = data[0][0][0]

            return translated
    except Exception as e:
        print(f"Translation failed: {e}")
        return text


def make_disposition(filename: str):
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
    encoded = urllib.parse.quote(safe, safe="")
    return f"attachment: filename=\"{filename}\"; filename*=utf-8''{encoded}"
