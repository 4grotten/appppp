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


# Model configuration
GEMINI_TEXT_MODEL_FILE = os.environ.get("GEMINI_TEXT_MODEL_FILE", "/app/.gemini_text_model")
GEMINI_IMAGE_MODEL_FILE = os.environ.get("GEMINI_IMAGE_MODEL_FILE", "/app/.gemini_image_model")

_CACHED_TEXT_MODEL = None
_CACHED_IMAGE_MODEL = None


def get_gemini_text_model():
    global _CACHED_TEXT_MODEL
    
    if _CACHED_TEXT_MODEL:
        return _CACHED_TEXT_MODEL
    
    try:
        if os.path.exists(GEMINI_TEXT_MODEL_FILE):
            with open(GEMINI_TEXT_MODEL_FILE, "r") as f:
                model = f.read().strip()
                if model:
                    _CACHED_TEXT_MODEL = model
                    return model
    except Exception:
        pass
    
    return config("GEMINI_TEXT_MODEL", default="gemini-2.5-pro")


def set_gemini_text_model(model_name: str):
    global _CACHED_TEXT_MODEL
    
    _CACHED_TEXT_MODEL = model_name
    
    try:
        os.makedirs(os.path.dirname(GEMINI_TEXT_MODEL_FILE), exist_ok=True)
        with open(GEMINI_TEXT_MODEL_FILE, "w") as f:
            f.write(model_name)
        print(f"Text model successfully updated and saved to {GEMINI_TEXT_MODEL_FILE}")
    except Exception as e:
        print(f"Failed to save text model to file: {e}")


def get_gemini_image_model():
    global _CACHED_IMAGE_MODEL
    
    if _CACHED_IMAGE_MODEL:
        return _CACHED_IMAGE_MODEL
    
    try:
        if os.path.exists(GEMINI_IMAGE_MODEL_FILE):
            with open(GEMINI_IMAGE_MODEL_FILE, "r") as f:
                model = f.read().strip()
                if model:
                    _CACHED_IMAGE_MODEL = model
                    return model
    except Exception:
        pass
    
    return config("GEMINI_IMAGE_MODEL", default="gemini-2.5-pro")


def set_gemini_image_model(model_name: str):
    global _CACHED_IMAGE_MODEL
    
    _CACHED_IMAGE_MODEL = model_name
    
    try:
        os.makedirs(os.path.dirname(GEMINI_IMAGE_MODEL_FILE), exist_ok=True)
        with open(GEMINI_IMAGE_MODEL_FILE, "w") as f:
            f.write(model_name)
        print(f"Image model successfully updated and saved to {GEMINI_IMAGE_MODEL_FILE}")
    except Exception as e:
        print(f"Failed to save image model to file: {e}")
