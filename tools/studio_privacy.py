"""Shared publication checks for fictional studio record email addresses."""

import html
import re
from urllib.parse import unquote

EMAIL_RE = re.compile(
    r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@(?:[a-z0-9-]+\.)+[a-z]{2,}",
    re.IGNORECASE,
)


def reserved_email(address: str) -> bool:
    if not EMAIL_RE.fullmatch(address):
        return False
    domain = address.rsplit("@", 1)[1].lower()
    return (domain == "example.com" or domain.endswith(".example.com")
            or domain.endswith(".test") or domain.endswith(".invalid"))


def has_unapproved_email(text: str) -> bool:
    decoded = unquote(html.unescape(text))
    return any(not reserved_email(match[0]) for match in EMAIL_RE.finditer(decoded))
