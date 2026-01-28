import redis
from django.conf import settings

# Redis 4.6+ has built-in connection pooling by default
# Adding socket timeouts for resilience against slow/hung connections
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_timeout=5,          # Read/write timeout (seconds)
    socket_connect_timeout=5,  # Connection timeout (seconds)
)
