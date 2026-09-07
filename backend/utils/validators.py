import re
from urllib.parse import urlparse

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_IG_POST_SHORTCODE_REGEX = re.compile(r"^[A-Za-z0-9_-]{5,30}$")


def is_valid_email(email: str) -> bool:
    """Checks if string looks like a valid email address."""
    if not email or not isinstance(email, str):
        return False
    return bool(_EMAIL_REGEX.match(email.strip()))


def is_valid_url(url: str) -> bool:
    """Checks if string has a valid URL scheme and netloc."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        return bool(parsed.scheme in ("http", "https") and parsed.netloc)
    except Exception:
        return False


def is_valid_instagram_id(id_str: str) -> bool:
    """Checks if string is a plausible Instagram post ID or shortcode."""
    if not id_str or not isinstance(id_str, str):
        return False
    clean = id_str.strip()
    return bool(_IG_POST_SHORTCODE_REGEX.match(clean) or clean.isdigit())
