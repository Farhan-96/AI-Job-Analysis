"""Profile classification from job title + description signals."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import MatchLevel
from app.models.profile import ResumeProfile
from app.services.skill_extraction import ExtractedSkill


@dataclass(frozen=True)
class ProfileClassification:
    profile_id: int
    profile_slug: str
    profile_name: str
    role_match: str
    matching_keywords: list[str]
    missing_keywords: list[str]
    title_score: float
    skill_overlap_score: float


def _title_role_score(title: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    title_lower = title.lower()
    matched: list[str] = []
    missing: list[str] = []
    for keyword in keywords:
        if keyword.lower() in title_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)
    if not keywords:
        return 0.0, matched, missing
    ratio = len(matched) / len(keywords)
    # Strong title hit if any high-signal keyword matches
    if matched:
        ratio = max(ratio, 0.55 if len(matched) == 1 else min(1.0, 0.4 + 0.3 * len(matched)))
    return ratio, matched, missing


def _skill_overlap(
    extracted: list[ExtractedSkill],
    profile: ResumeProfile,
) -> float:
    if not profile.skills:
        return 0.0
    extracted_names = {s.skill.lower() for s in extracted}
    total_weight = sum(s.weight for s in profile.skills) or 1.0
    matched_weight = sum(
        s.weight for s in profile.skills if s.skill.lower() in extracted_names
    )
    return matched_weight / total_weight


def role_level_from_score(score: float) -> str:
    if score >= 0.65:
        return MatchLevel.HIGH.value
    if score >= 0.35:
        return MatchLevel.MEDIUM.value
    if score > 0:
        return MatchLevel.LOW.value
    return MatchLevel.LOW.value


def classify_profiles(
    *,
    title: str,
    description: str,
    extracted_skills: list[ExtractedSkill],
    profiles: list[ResumeProfile],
) -> list[ProfileClassification]:
    """Score all active profiles; does not pick a single winner."""
    results: list[ProfileClassification] = []
    text = f"{title}\n{description}".lower()

    for profile in profiles:
        if not profile.active:
            continue
        keywords = [str(k) for k in (profile.title_keywords or [])]
        title_score, matched_kw, missing_kw = _title_role_score(title, keywords)

        # Description keyword boost
        desc_hits = [k for k in keywords if k.lower() in text]
        if desc_hits and title_score < 0.55:
            title_score = max(title_score, min(0.6, 0.25 + 0.1 * len(desc_hits)))
            for k in desc_hits:
                if k not in matched_kw:
                    matched_kw.append(k)
                    if k in missing_kw:
                        missing_kw.remove(k)

        skill_score = _skill_overlap(extracted_skills, profile)
        combined = 0.65 * title_score + 0.35 * skill_score

        results.append(
            ProfileClassification(
                profile_id=profile.id,
                profile_slug=profile.slug,
                profile_name=profile.name,
                role_match=role_level_from_score(combined),
                matching_keywords=matched_kw,
                missing_keywords=missing_kw[:10],
                title_score=round(title_score, 3),
                skill_overlap_score=round(skill_score, 3),
            )
        )

    return results
