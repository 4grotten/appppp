"""Shared HTTP client for Telegram Bot API requests.

Provides connection pooling to avoid TCP/TLS overhead on each request.
Thread-safe singleton session with automatic retries.

Features:
- Connection pooling (20 connections to api.telegram.org)
- Automatic retries on 429/502/503/504 with exponential backoff
- Respects Retry-After header for rate limiting
- Thread-safe singleton pattern
"""

import logging
import threading
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Thread-safe singleton
_session: Optional[requests.Session] = None
_session_lock = threading.Lock()

# Default timeout for Telegram API requests (connect, read)
DEFAULT_TIMEOUT = (5, 30)  # 5 sec connect, 30 sec read

# Telegram API base URL
TELEGRAM_API_BASE = "https://api.telegram.org"


def get_telegram_session() -> requests.Session:
    """Get shared HTTP session for Telegram Bot API requests.

    Returns a thread-safe singleton Session with:
    - Connection pooling (20 connections to api.telegram.org)
    - Automatic retries on 429/502/503/504
    - Respects Retry-After header

    Returns:
        Configured requests.Session instance
    """
    global _session

    if _session is not None:
        return _session

    with _session_lock:
        # Double-check locking pattern
        if _session is not None:
            return _session

        session = requests.Session()

        # Configure retry strategy with rate limit handling
        # Telegram returns 429 with Retry-After header when rate limited
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,  # 0.5, 1.0, 2.0 seconds (exponential)
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,  # Honor Retry-After from Telegram
            raise_on_status=False,
        )

        # Configure connection pooling
        # Telegram has one host (api.telegram.org), so we need fewer pools
        adapter = HTTPAdapter(
            pool_connections=5,    # Number of urllib3 connection pools
            pool_maxsize=20,       # Max connections per pool
            pool_block=True,       # Block when pool is full
            max_retries=retry_strategy,
        )

        session.mount("https://", adapter)

        logger.info("[TG_HTTP] Initialized shared session with connection pooling")
        _session = session

    return _session


def close_telegram_session() -> None:
    """Close the shared session (for graceful shutdown)."""
    global _session

    with _session_lock:
        if _session is not None:
            _session.close()
            _session = None
            logger.info("[TG_HTTP] Closed shared session")


def telegram_request(
    method: str,
    url: str,
    timeout: tuple = None,
    **kwargs,
) -> requests.Response:
    """Make HTTP request to Telegram API with default timeout.

    Wrapper around session.request() that ensures timeout is always set.

    Args:
        method: HTTP method (GET, POST)
        url: Full URL to request
        timeout: Optional custom timeout (connect, read). Default: (5, 30)
        **kwargs: Additional arguments passed to session.request()

    Returns:
        requests.Response object

    Raises:
        requests.exceptions.Timeout: On timeout
        requests.exceptions.RequestException: On other network errors
    """
    session = get_telegram_session()
    return session.request(
        method=method,
        url=url,
        timeout=timeout or DEFAULT_TIMEOUT,
        **kwargs,
    )


def telegram_post(
    url: str,
    json: Dict = None,
    data: Dict = None,
    files: Dict = None,
    timeout: tuple = None,
) -> requests.Response:
    """Make POST request to Telegram API.

    Convenience wrapper for the most common use case.

    Args:
        url: Full URL to request
        json: JSON body (for sendMessage, etc.)
        data: Form data (for file uploads)
        files: Files to upload
        timeout: Optional custom timeout

    Returns:
        requests.Response object
    """
    session = get_telegram_session()
    return session.post(
        url=url,
        json=json,
        data=data,
        files=files,
        timeout=timeout or DEFAULT_TIMEOUT,
    )


def get_pool_status() -> Dict[str, Any]:
    """Get connection pool statistics for monitoring.

    Returns:
        Dict with pool health information
    """
    global _session

    if _session is None:
        return {"initialized": False, "pools": []}

    pool_stats = []

    for prefix, adapter in _session.adapters.items():
        if not hasattr(adapter, "poolmanager"):
            continue

        pm = adapter.poolmanager
        if pm is None:
            continue

        for pool_key, pool in pm.pools.items():
            stats = {
                "host": f"{pool_key.scheme}://{pool_key.host}:{pool_key.port}",
                "num_connections": getattr(pool, "num_connections", 0),
                "num_requests": getattr(pool, "num_requests", 0),
            }
            if hasattr(pool, "pool") and pool.pool is not None:
                stats["free_connections"] = pool.pool.qsize()
            pool_stats.append(stats)

    return {
        "initialized": True,
        "pools": pool_stats,
    }
