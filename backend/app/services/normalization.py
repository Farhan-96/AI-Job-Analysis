"""Job title, location, employment, and remote-type normalization."""

from __future__ import annotations

import re

from app.data.skill_dictionary import TITLE_ALIASES
from app.models.enums import RemoteType


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def normalize_title(title: str) -> str:
    cleaned = normalize_whitespace(title)
    alias = TITLE_ALIASES.get(cleaned.lower())
    if alias:
        return alias
    # Expand a few common abbreviations without inventing roles
    cleaned = re.sub(r"\bRN\b", "React Native", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bEng\.\b", "Engineer", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bDev\b", "Developer", cleaned, flags=re.IGNORECASE)
    return normalize_whitespace(cleaned)


def normalize_company(company: str | None) -> str | None:
    if not company:
        return None
    return normalize_whitespace(company)


def normalize_location(location: str | None) -> str | None:
    if not location:
        return None
    cleaned = normalize_whitespace(location)
    mapping = {
        "isb": "Islamabad",
        "rwp": "Rawalpindi",
        "lhr": "Lahore",
        "khi": "Karachi",
        "pk": "Pakistan",
    }
    lower = cleaned.lower()
    return mapping.get(lower, cleaned)


def detect_remote_type(location: str | None, description: str) -> str:
    text = f"{location or ''} {description}".lower()
    if re.search(r"\bremote\b|\bwork from home\b|\bwfh\b", text):
        if re.search(r"\bhybrid\b", text):
            return RemoteType.HYBRID.value
        return RemoteType.REMOTE.value
    if re.search(r"\bhybrid\b", text):
        return RemoteType.HYBRID.value
    if re.search(r"\bonsite\b|\bon-site\b|\bin[- ]office\b|\bin office\b", text):
        return RemoteType.ONSITE.value
    if location and location.strip():
        # Named city without remote keywords → treat as onsite
        return RemoteType.ONSITE.value
    return RemoteType.UNKNOWN.value


def normalize_employment_type(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = normalize_whitespace(value).lower()
    mapping = {
        "ft": "full-time",
        "full time": "full-time",
        "fulltime": "full-time",
        "pt": "part-time",
        "part time": "part-time",
        "contract": "contract",
        "internship": "internship",
        "temp": "temporary",
    }
    return mapping.get(cleaned, cleaned)


_SALARY_PATTERN = re.compile(
    r"(?P<currency>USD|PKR|\$|Rs\.?)?\s*"
    r"(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?P<suffix>k|K)?",
    re.IGNORECASE,
)


def parse_salary_range(
    text: str | None,
) -> tuple[float | None, float | None, str | None]:
    """Best-effort salary extraction from free text. Returns (min, max, currency)."""
    if not text:
        return None, None, None
    matches = list(_SALARY_PATTERN.finditer(text))
    if not matches:
        return None, None, None

    amounts: list[float] = []
    currency: str | None = None
    for match in matches[:4]:
        raw = match.group("amount").replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        if match.group("suffix"):
            value *= 1000
        amounts.append(value)
        cur = match.group("currency")
        if cur:
            currency = "USD" if cur.strip() == "$" else cur.strip().upper().replace(".", "")
    if not amounts:
        return None, None, None
    return min(amounts), max(amounts), currency
