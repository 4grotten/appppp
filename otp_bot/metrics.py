"""Simple timing metrics for OTP Bot performance monitoring."""

import time
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


def track_timing(operation_name: str):
    """Decorator to log execution time of a function."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"[TIMING] {operation_name}: {elapsed_ms:.1f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"[TIMING] {operation_name}: {elapsed_ms:.1f}ms (error: {type(e).__name__})")
                raise
        return wrapper
    return decorator
