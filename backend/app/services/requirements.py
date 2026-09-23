"""Experience and education requirement extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExperienceRequirement:
    years: float | None
    fresh_ok: bool
    raw: str | None


@dataclass(frozen=True)
class EducationRequirement:
    level: str | None
    raw: str | None


_YEARS_PATTERNS = [
    re.compile(
        r"(?P<years>\d+(?:\.\d+)?)\s*\+?\s*(?:\+|plus)?\s*years?(?:\s+of)?\s+(?:experience|exp\.?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:experience|exp\.?)\s*(?:of|:)?\s*(?P<years>\d+(?:\.\d+)?)\s*\+?\s*years?",
        re.IGNORECASE,
    ),
    re.compile(r"(?P<years>\d+)\s*\+\s*years?", re.IGNORECASE),
]

_FRESH_PATTERN = re.compile(
    r"fresh\s+(?:graduates?|ers?)|entry[- ]level|no\s+experience\s+required|0\s*[-–]\s*1\s*years?",
    re.IGNORECASE,
)

_EDUCATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"master'?s(?:\s+degree)?|msc|ms\b|m\.s\.", re.IGNORECASE), "masters"),
    (
        re.compile(
            r"bachelor'?s(?:\s+degree)?|bachelors|bsc|bs\b|b\.s\.|be\b|b\.e\.",
            re.IGNORECASE,
        ),
        "bachelors",
    ),
    (
        re.compile(
            r"bachelor'?s?\s+(?:in\s+)?(?:computer science|information technology|it|cs|software)",
            re.IGNORECASE,
        ),
        "bachelors_cs_it",
    ),
    (re.compile(r"phd|doctorate", re.IGNORECASE), "phd"),
    (re.compile(r"associate(?:'s)?\s+degree|diploma", re.IGNORECASE), "associate_or_diploma"),
]


def extract_experience(text: str) -> ExperienceRequirement:
    fresh_ok = bool(_FRESH_PATTERN.search(text))
    years: float | None = None
    raw: str | None = None
    for pattern in _YEARS_PATTERNS:
        match = pattern.search(text)
        if match:
            years = float(match.group("years"))
            raw = match.group(0)
            break
    return ExperienceRequirement(years=years, fresh_ok=fresh_ok, raw=raw)


def extract_education(text: str) -> EducationRequirement:
    # Prefer more specific CS/IT bachelor match when present
    for pattern, level in _EDUCATION_PATTERNS:
        match = pattern.search(text)
        if match and level == "bachelors_cs_it":
            return EducationRequirement(level=level, raw=match.group(0))
    for pattern, level in _EDUCATION_PATTERNS:
        match = pattern.search(text)
        if match:
            return EducationRequirement(level=level, raw=match.group(0))
    return EducationRequirement(level=None, raw=None)


def compare_experience(
    required: ExperienceRequirement,
    profile_min: float | None,
    profile_max: float | None,
) -> str:
    """Return high|medium|low|unknown|true|false style match label."""
    if required.years is None and not required.fresh_ok:
        return "unknown"
    if required.fresh_ok and (profile_min is None or profile_min <= 1):
        return "high"
    if required.years is None:
        return "unknown"
    if profile_min is None and profile_max is None:
        return "unknown"
    candidate_min = profile_min if profile_min is not None else 0.0
    candidate_max = profile_max if profile_max is not None else candidate_min + 10
    if candidate_min <= required.years <= candidate_max or candidate_max >= required.years:
        # Profile experience band covers or exceeds the requirement
        if candidate_max >= required.years and candidate_min <= required.years + 2:
            return "high"
        return "medium"
    if candidate_max < required.years:
        return "low"
    return "medium"


def compare_education(
    required: EducationRequirement,
    profile_keywords: list[str],
) -> str:
    if required.level is None:
        return "unknown"
    if not profile_keywords:
        return "unknown"
    normalized_profile = " ".join(k.lower() for k in profile_keywords)
    level = required.level
    if level in {"bachelors", "bachelors_cs_it"}:
        if any(k in normalized_profile for k in ("bachelor", "bs", "bsc", "computer", "it")):
            return "high"
        return "medium"
    if level == "masters":
        if "master" in normalized_profile or "msc" in normalized_profile:
            return "high"
        if "bachelor" in normalized_profile:
            return "medium"
        return "low"
    if level == "phd":
        return "high" if "phd" in normalized_profile else "low"
    return "medium"
