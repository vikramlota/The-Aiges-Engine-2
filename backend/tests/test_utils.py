from backend.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.utils.helpers import (
    sanitize_handle,
    truncate_text,
    exponential_backoff_retry,
    utc_now,
)
from backend.utils.validators import (
    is_valid_email,
    is_valid_url,
    is_valid_instagram_id,
)


def test_password_hashing_and_verification():
    pw = "supersecret123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpw", hashed) is False


def test_access_token_lifecycle():
    data = {"sub": "user@aiges.ai", "role": "admin"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "user@aiges.ai"
    assert payload.get("role") == "admin"

    # Invalid token decode returns None
    assert decode_access_token("invalid.token.payload") is None


def test_helpers_sanitization_and_truncation():
    # Handle sanitization
    assert sanitize_handle("creator_1") == "@creator_1"
    assert sanitize_handle("  @creator_2  ") == "@creator_2"
    assert sanitize_handle("") == ""

    # Truncation
    short_text = "Hello world"
    assert truncate_text(short_text, max_chars=20) == "Hello world"
    long_text = "This is a very long string that will definitely exceed the limit of characters"
    truncated = truncate_text(long_text, max_chars=25)
    assert len(truncated) <= 25
    assert truncated.endswith("...")

    # utc_now returns aware datetime
    now = utc_now()
    assert now.tzinfo is not None


def test_exponential_backoff_retry():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("Temporary failure")
        return "success"

    res = exponential_backoff_retry(flaky, max_retries=3, base_delay=0.01)
    assert res == "success"
    assert len(calls) == 3


def test_validators():
    # Email
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("invalid-email") is False
    assert is_valid_email("") is False

    # URL
    assert is_valid_url("https://instagram.com/p/12345") is True
    assert is_valid_url("http://youtube.com/watch?v=abc") is True
    assert is_valid_url("just a string") is False

    # Instagram ID
    assert is_valid_instagram_id("C8kJ9zLox12") is True
    assert is_valid_instagram_id("123456789") is True
    assert is_valid_instagram_id("!") is False
