import re
import time
from datetime import datetime, timezone
from typing import Callable, Any, TypeVar

T = TypeVar("T")


def utc_now() -> datetime:
    """Returns current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def sanitize_handle(handle: str) -> str:
    """
    Sanitizes social media handle:
    - Trims whitespace
    - Ensures leading '@'
    """
    if not handle:
        return ""
    clean = handle.strip()
    if not clean.startswith("@"):
        clean = f"@{clean}"
    return clean


def truncate_text(text: str, max_chars: int = 120, ellipsis: str = "...") -> str:
    """Safely truncate text to a maximum length with ellipsis."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[: max_chars - len(ellipsis)].rstrip() + ellipsis


def exponential_backoff_retry(
    fn: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (Exception,)
) -> T:
    """
    Executes a function with exponential backoff on retryable exceptions.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except retryable_exceptions as e:
            if attempt == max_retries - 1:
                raise e
            sleep_time = base_delay * (2 ** attempt)
            time.sleep(sleep_time)
    raise RuntimeError("Retry loop exhausted unexpectedly")
