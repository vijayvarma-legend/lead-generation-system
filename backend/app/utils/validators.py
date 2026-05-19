"""Input validation utilities."""

from __future__ import annotations

import re
from urllib.parse import urlparse


_URL_RE = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
    r"localhost|\d{1,3}(?:\.\d{1,3}){3})"
    r"(?::\d+)?(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_valid_url(url: str | None) -> bool:
    if not url:
        return False
    return bool(_URL_RE.match(url))


def normalise_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
        return url if parsed.netloc else None
    except Exception:
        return None


def is_valid_phone(phone: str | None) -> bool:
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15
