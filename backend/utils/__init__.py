"""
Backend utilities package for The Aiges Engine.
Provides security, validation, and common helper functions.
"""

from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.utils.helpers import (
    utc_now,
    sanitize_handle,
    truncate_text,
    exponential_backoff_retry,
)
from backend.utils.validators import (
    is_valid_email,
    is_valid_url,
    is_valid_instagram_id,
)

__all__ = [
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    # Helpers
    "utc_now",
    "sanitize_handle",
    "truncate_text",
    "exponential_backoff_retry",
    # Validators
    "is_valid_email",
    "is_valid_url",
    "is_valid_instagram_id",
]
