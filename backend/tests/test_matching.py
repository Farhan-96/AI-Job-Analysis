"""Matching engine unit tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.profile_repository import list_profiles
from app.seed import seed_profiles
from app.services.classification import ProfileClassification, classify_profiles
from app.services.location_matching import compare_location
from app.services.matching import compute_match
from app.services.requirements import (
    EducationRequirement,
    ExperienceRequirement,
    compare_education,
    compare_experience,
    extract_education,
    extract_experience,
)
from app.services.skill_extraction import extract_skills
from tests.sample_jobs import RN_JOB


def test_skill_extraction() -> None:
    skills = extract_skills(
        "React Native Developer",
        "Need React Native, TypeScript, Expo, REST APIs, Firebase, Node JS, Postgres",
    )
    names = {s.skill for s in skills}
    assert "React Native" in names
    assert "TypeScript" in names
    assert "Expo" in names
    assert "REST API" in names
    assert "Firebase" in names
    assert "Node.js" in names
    assert "PostgreSQL" in names


def test_experience_matching() -> None:
    req = extract_experience("2+ years React Native experience required")
    assert req.years == 2.0
    assert compare_experience(req, 1, 8) == "high"
    assert compare_experience(ExperienceRequirement(None, False, None), 1, 8) == "unknown"


def test_education_matching() -> None:
    edu = extract_education("Bachelor's degree in Computer Science preferred")
    assert edu.level is not None
    assert compare_education(edu, ["Bachelor", "BS Computer Science"]) == "high"
    assert compare_education(EducationRequirement(None, None), ["Bachelor"]) == "unknown"


def test_location_matching() -> None:
    assert (
        compare_location(
            remote_type="remote",
            location="Remote",
            preferred_locations=["Islamabad"],
            remote_ok=True,
        )
        == "true"
    )
    assert (
        compare_location(
            remote_type="onsite",
            location="Islamabad",
            preferred_locations=["Islamabad", "Rawalpindi"],
            remote_ok=True,
        )
        == "true"
    )
    assert (
        compare_location(
            remote_type="onsite",
            location="Lahore",
            preferred_locations=["Islamabad"],
            remote_ok=False,
        )
        == "false"
    )


def test_profile_classification_react_native(db_session: Session) -> None:
    seed_profiles(db_session)
    profiles = list_profiles(db_session, active_only=True)
    skills = extract_skills(RN_JOB["title"], RN_JOB["description"])
    results = classify_profiles(
        title=RN_JOB["title"],
        description=RN_JOB["description"],
        extracted_skills=skills,
        profiles=profiles,
    )
    by_slug = {r.profile_slug: r for r in results}
    assert by_slug["react-native"].role_match == "high"
    assert by_slug["ai-python"].role_match in {"low", "medium"}


def test_matching_score_components(db_session: Session) -> None:
    seed_profiles(db_session)
    profile = next(p for p in list_profiles(db_session) if p.slug == "react-native")
    skills = extract_skills(RN_JOB["title"], RN_JOB["description"])
    classification = ProfileClassification(
        profile_id=profile.id,
        profile_slug=profile.slug,
        profile_name=profile.name,
        role_match="high",
        matching_keywords=["React Native"],
        missing_keywords=[],
        title_score=0.9,
        skill_overlap_score=0.8,
    )
    result = compute_match(
        profile=profile,
        classification=classification,
        extracted_skills=skills,
        experience=extract_experience(RN_JOB["description"]),
        education=extract_education(RN_JOB["description"]),
        remote_type="remote",
        location="Remote",
    )
    assert 0 <= result.match_score <= 100
    assert "React Native" in result.matching_skills
    assert result.score_breakdown is not None
    assert "role" in result.score_breakdown
    assert result.role_match == "high"
