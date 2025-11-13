from decouple import config

GEMINI_API_KEY: str = config("GEMINI_API_KEY")
PROXY_USER = "gemini_proxy"
PROXY_PASS = config("PROXY_PASS")
PROXY_HOST = config("PROXY_HOST")
PROXY_PORT = "1080"
