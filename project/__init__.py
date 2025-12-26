import requests.adapters

from .celery import app as celery_app

__all__ = ["celery_app"]

requests.adapters.DEFAULT_POOLSIZE = 100
requests.adapters.DEFAULT_RETRIES = 3
print("Connection pool size patched to 100")
