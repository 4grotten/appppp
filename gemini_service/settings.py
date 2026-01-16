import os

from decouple import config

GEMINI_API_KEY_FILE = os.environ.get("GEMINI_API_KEY_FILE", "/app/.gemini_api_key")

_GEMINI_API_KEY_FALLBACK = config("GEMINI_API_KEY", default="")

_CACHED_API_KEY = None

def get_gemini_api_key():
    global _CACHED_API_KEY
    

    if _CACHED_API_KEY:
        return _CACHED_API_KEY

    try:
        if os.path.exists(GEMINI_API_KEY_FILE):
            with open(GEMINI_API_KEY_FILE, "r") as f:
                key = f.read().strip()
                if key:
                    _CACHED_API_KEY = key
                    return key
    except Exception:
        pass

    return _GEMINI_API_KEY_FALLBACK

def set_gemini_api_key(new_key: str):
    global _CACHED_API_KEY
    
    _CACHED_API_KEY = new_key
 
    try:
        os.makedirs(os.path.dirname(GEMINI_API_KEY_FILE), exist_ok=True)
        
        with open(GEMINI_API_KEY_FILE, "w") as f:
            f.write(new_key)
        print(f"API Key successfully updated and saved to {GEMINI_API_KEY_FILE}")
    except Exception as e:
        print(f"Failed to save API key to file: {e}")


PROXY_USER = "gemini_proxy"
PROXY_PASS = config("PROXY_PASS", None)
PROXY_HOST = config("PROXY_HOST", None)
PROXY_PORT = "1080"
PRODUCTION = config("PRODUCTION", False, cast=bool)
