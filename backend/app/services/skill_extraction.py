"""Deterministic skill extraction from job text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.data.skill_dictionary import ALIAS_TO_CANONICAL, SKILL_ALIASES


@dataclass(frozen=True)
class ExtractedSkill:
    skill: str
    source: str
    confidence: float


def _normalize_text(text: str) -> str:
    # Unify separators for easier matching
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def extract_skills(title: str, description: str) -> list[ExtractedSkill]:
    """
    Extract canonical skills using the configurable dictionary.

    Matching is deterministic (no LLM). Longer aliases are preferred
    to avoid partial collisions (e.g. React Native before React).
    """
    combined = _normalize_text(f"{title}\n{description}")
    found: dict[str, ExtractedSkill] = {}

    # Sort aliases by length descending so "react native" beats "react"
    aliases = sorted(ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)
    occupied: list[tuple[int, int]] = []

    for alias in aliases:
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", re.IGNORECASE)
        for match in pattern.finditer(combined):
            start, end = match.span()
            if any(start < o_end and end > o_start for o_start, o_end in occupied):
                continue
            canonical = ALIAS_TO_CANONICAL[alias]
            occupied.append((start, end))
            if canonical not in found:
                confidence = 1.0 if alias == canonical.lower() else 0.9
                found[canonical] = ExtractedSkill(
                    skill=canonical,
                    source="dictionary",
                    confidence=confidence,
                )

    return list(found.values())


def all_known_skills() -> list[str]:
    return sorted(SKILL_ALIASES.keys())
