import os

from decouple import config

GEMINI_API_KEY_FILE = os.environ.get(
	"GEMINI_API_KEY_FILE", "/etc/gemini/api_key"
)

_GEMINI_API_KEY_FALLBACK = config("GEMINI_API_KEY", default="")

def get_gemini_api_key():
	try:
		if os.path.exists(GEMINI_API_KEY_FILE):
			with open(GEMINI_API_KEY_FILE, "r") as f:
				return f.read().strip()
	except Exception:
		pass
	return _GEMINI_API_KEY_FALLBACK

PROXY_USER = "gemini_proxy"
PROXY_PASS = config("PROXY_PASS", None)
PROXY_HOST = config("PROXY_HOST", None)
PROXY_PORT = "1080"
PRODUCTION = config("PRODUCTION", False, cast=bool)
