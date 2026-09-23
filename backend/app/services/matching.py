"""Transparent profile match scoring engine."""

from __future__ import annotations

from dataclasses import dataclass

from app.data.skill_dictionary import DEFAULT_MATCH_WEIGHTS
from app.models.enums import MatchLevel
from app.models.profile import ResumeProfile
from app.services.classification import ProfileClassification
from app.services.location_matching import compare_location
from app.services.requirements import (
    EducationRequirement,
    ExperienceRequirement,
    compare_education,
    compare_experience,
)
from app.services.skill_extraction import ExtractedSkill


@dataclass(frozen=True)
class MatchResult:
    profile_id: int
    match_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    matching_keywords: list[str]
    missing_keywords: list[str]
    experience_match: str
    education_match: str
    role_match: str
    location_match: str
    salary_match: str
    analysis: str
    recommendation: str
    score_breakdown: dict[str, float]


def _level_to_score(level: str) -> float:
    mapping = {
        MatchLevel.HIGH.value: 1.0,
        MatchLevel.MEDIUM.value: 0.6,
        MatchLevel.LOW.value: 0.25,
        MatchLevel.TRUE.value: 1.0,
        MatchLevel.FALSE.value: 0.0,
        MatchLevel.UNKNOWN.value: 0.5,
        "unknown": 0.5,
        "true": 1.0,
        "false": 0.0,
    }
    return mapping.get(level, 0.5)


def _resolve_weights(profile: ResumeProfile) -> dict[str, float]:
    weights = dict(DEFAULT_MATCH_WEIGHTS)
    if profile.match_weights:
        for key, value in profile.match_weights.items():
            if key in weights and isinstance(value, (int, float)):
                weights[key] = float(value)
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def _skills_component(
    extracted: list[ExtractedSkill],
    profile: ResumeProfile,
) -> tuple[float, list[str], list[str]]:
    if not profile.skills:
        return 0.5, [], []
    extracted_map = {s.skill.lower(): s.skill for s in extracted}
    matching: list[str] = []
    missing: list[str] = []
    total_weight = sum(s.weight for s in profile.skills) or 1.0
    matched_weight = 0.0
    for skill in profile.skills:
        if skill.skill.lower() in extracted_map:
            matching.append(skill.skill)
            matched_weight += skill.weight
        else:
            missing.append(skill.skill)
            if skill.required:
                # Required misses already reflected via lower matched_weight
                pass
    return matched_weight / total_weight, matching, missing


def compute_match(
    *,
    profile: ResumeProfile,
    classification: ProfileClassification,
    extracted_skills: list[ExtractedSkill],
    experience: ExperienceRequirement,
    education: EducationRequirement,
    remote_type: str,
    location: str | None,
) -> MatchResult:
    weights = _resolve_weights(profile)
    skills_score, matching_skills, missing_skills = _skills_component(
        extracted_skills, profile
    )
    role_match = classification.role_match
    experience_match = compare_experience(
        experience, profile.min_experience_years, profile.max_experience_years
    )
    education_match = compare_education(
        education, [str(k) for k in (profile.education_keywords or [])]
    )
    location_match = compare_location(
        remote_type=remote_type,
        location=location,
        preferred_locations=[str(x) for x in (profile.preferred_locations or [])],
        remote_ok=profile.remote_ok,
    )
    salary_match = "unknown"

    breakdown = {
        "role": round(_level_to_score(role_match) * 100, 2),
        "skills": round(skills_score * 100, 2),
        "experience": round(_level_to_score(experience_match) * 100, 2),
        "education": round(_level_to_score(education_match) * 100, 2),
        "location": round(_level_to_score(location_match) * 100, 2),
    }

    total = (
        weights["role"] * _level_to_score(role_match)
        + weights["skills"] * skills_score
        + weights["experience"] * _level_to_score(experience_match)
        + weights["education"] * _level_to_score(education_match)
        + weights["location"] * _level_to_score(location_match)
    )
    match_score = round(total * 100, 1)

    if match_score >= 75:
        recommendation = "strong_fit"
    elif match_score >= 55:
        recommendation = "review"
    else:
        recommendation = "weak_fit"

    analysis_parts = [
        f"Profile Match Score {match_score}/100 for {profile.name}.",
        f"Role match: {role_match} (title signals + skill overlap).",
        f"Skills matched: {len(matching_skills)}; missing: {len(missing_skills)}.",
        f"Experience: {experience_match}; Education: {education_match}; Location: {location_match}.",
    ]
    if experience.raw:
        analysis_parts.append(f"Job experience requirement detected: {experience.raw}.")
    if education.raw:
        analysis_parts.append(f"Job education requirement detected: {education.raw}.")

    return MatchResult(
        profile_id=profile.id,
        match_score=match_score,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        matching_keywords=classification.matching_keywords,
        missing_keywords=classification.missing_keywords,
        experience_match=experience_match,
        education_match=education_match,
        role_match=role_match,
        location_match=location_match,
        salary_match=salary_match,
        analysis=" ".join(analysis_parts),
        recommendation=recommendation,
        score_breakdown=breakdown,
    )
