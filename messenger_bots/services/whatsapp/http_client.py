"""Shared HTTP client for WAHA API requests.

Provides connection pooling to avoid TCP/TLS overhead on each request.
Thread-safe singleton session with automatic retries.

Features:
- Connection pooling (50 connections per host)
- Automatic retries on 429/502/503/504 with exponential backoff
- Respects Retry-After header for rate limiting
- Thread-safe singleton pattern
- Health check for pool monitoring
"""

import logging
import threading
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

logger = logging.getLogger(__name__)

# Thread-safe singleton
_session: Optional[requests.Session] = None
_session_lock = threading.Lock()

# Default timeout for all WAHA requests (connect, read)
DEFAULT_TIMEOUT = (5, 30)  # 5 sec connect, 30 sec read


def get_waha_session() -> requests.Session:
    """Get shared HTTP session for WAHA API requests.

    Returns a thread-safe singleton Session with:
    - Connection pooling (50 connections to WAHA host)
    - Automatic retries on 502/503/504
    - Pre-configured API key header

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
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,  # 0.5, 1.0, 2.0 seconds (exponential)
            status_forcelist=[429, 502, 503, 504],  # Include 429 rate limit
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            respect_retry_after_header=True,  # Honor Retry-After from WAHA
            raise_on_status=False,  # Don't raise on retry exhaustion, let caller handle
        )

        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,   # Number of urllib3 connection pools
            pool_maxsize=50,       # Max connections per pool (to WAHA)
            pool_block=True,       # Block when pool is full instead of creating new
            max_retries=retry_strategy,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        api_key = getattr(settings, "WAHA_API_KEY", "")
        session.headers.update({
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        })

        logger.info("[WAHA_HTTP] Initialized shared session with connection pooling")
        _session = session

    return _session


def close_waha_session() -> None:
    """Close the shared session (for graceful shutdown)."""
    global _session

    with _session_lock:
        if _session is not None:
            _session.close()
            _session = None
            logger.info("[WAHA_HTTP] Closed shared session")


def waha_request(
    method: str,
    url: str,
    timeout: tuple = None,
    **kwargs,
) -> requests.Response:
    """Make HTTP request to WAHA with default timeout.

    Wrapper around session.request() that ensures timeout is always set.
    Use this instead of calling session.request() directly.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request
        timeout: Optional custom timeout (connect, read). Default: (5, 30)
        **kwargs: Additional arguments passed to session.request()

    Returns:
        requests.Response object

    Raises:
        requests.exceptions.Timeout: On timeout
        requests.exceptions.RequestException: On other network errors
    """
    session = get_waha_session()
    return session.request(
        method=method,
        url=url,
        timeout=timeout or DEFAULT_TIMEOUT,
        **kwargs,
    )


def get_pool_status() -> Dict[str, Any]:
    """Get connection pool statistics for monitoring.

    Returns:
        Dict with pool health information:
        - initialized: bool - whether session exists
        - pools: list of pool stats per host
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

        # Get stats for each connection pool
        for pool_key, pool in pm.pools.items():
            stats = {
                "host": f"{pool_key.scheme}://{pool_key.host}:{pool_key.port}",
                "num_connections": getattr(pool, "num_connections", 0),
                "num_requests": getattr(pool, "num_requests", 0),
            }
            # Try to get queue size if available
            if hasattr(pool, "pool") and pool.pool is not None:
                stats["free_connections"] = pool.pool.qsize()
            pool_stats.append(stats)

    return {
        "initialized": True,
        "pools": pool_stats,
    }
