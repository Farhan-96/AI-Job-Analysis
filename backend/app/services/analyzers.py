"""Job analyzer abstractions — rule-based now, LLM-ready later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.profile import ResumeProfile
from app.services.classification import ProfileClassification, classify_profiles
from app.services.matching import MatchResult, compute_match
from app.services.normalization import (
    detect_remote_type,
    normalize_company,
    normalize_employment_type,
    normalize_location,
    normalize_title,
)
from app.services.requirements import (
    EducationRequirement,
    ExperienceRequirement,
    extract_education,
    extract_experience,
)
from app.services.skill_extraction import ExtractedSkill, extract_skills


@dataclass
class AnalysisResult:
    normalized_title: str
    company: str | None
    location: str | None
    remote_type: str
    employment_type: str | None
    skills: list[ExtractedSkill]
    experience: ExperienceRequirement
    education: EducationRequirement
    classifications: list[ProfileClassification]
    matches: list[MatchResult]


class JobAnalyzer(ABC):
    """Analyzer interface — RuleBased now; LLMJobAnalyzer later."""

    @abstractmethod
    def analyze(
        self,
        *,
        title: str,
        company: str | None,
        location: str | None,
        description: str,
        employment_type: str | None,
        remote_type: str | None,
        profiles: list[ResumeProfile],
    ) -> AnalysisResult:
        raise NotImplementedError


class RuleBasedJobAnalyzer(JobAnalyzer):
    """Deterministic pipeline: normalize → extract → classify → match."""

    def analyze(
        self,
        *,
        title: str,
        company: str | None,
        location: str | None,
        description: str,
        employment_type: str | None,
        remote_type: str | None,
        profiles: list[ResumeProfile],
    ) -> AnalysisResult:
        norm_title = normalize_title(title)
        norm_company = normalize_company(company)
        norm_location = normalize_location(location)
        norm_employment = normalize_employment_type(employment_type)
        detected_remote = remote_type or detect_remote_type(norm_location, description)

        skills = extract_skills(norm_title, description)
        experience = extract_experience(f"{norm_title}\n{description}")
        education = extract_education(description)

        classifications = classify_profiles(
            title=norm_title,
            description=description,
            extracted_skills=skills,
            profiles=profiles,
        )
        class_by_id = {c.profile_id: c for c in classifications}

        matches: list[MatchResult] = []
        for profile in profiles:
            if not profile.active:
                continue
            classification = class_by_id.get(profile.id)
            if classification is None:
                continue
            matches.append(
                compute_match(
                    profile=profile,
                    classification=classification,
                    extracted_skills=skills,
                    experience=experience,
                    education=education,
                    remote_type=detected_remote,
                    location=norm_location,
                )
            )

        return AnalysisResult(
            normalized_title=norm_title,
            company=norm_company,
            location=norm_location,
            remote_type=detected_remote,
            employment_type=norm_employment,
            skills=skills,
            experience=experience,
            education=education,
            classifications=classifications,
            matches=matches,
        )


class LLMJobAnalyzer(JobAnalyzer):
    """Placeholder for future LLM-assisted analysis. Not used in Phase 2."""

    def __init__(self, fallback: JobAnalyzer | None = None) -> None:
        self.fallback = fallback or RuleBasedJobAnalyzer()

    def analyze(
        self,
        *,
        title: str,
        company: str | None,
        location: str | None,
        description: str,
        employment_type: str | None,
        remote_type: str | None,
        profiles: list[ResumeProfile],
    ) -> AnalysisResult:
        # Phase 2: fall back to deterministic analysis (no LLM keys required)
        return self.fallback.analyze(
            title=title,
            company=company,
            location=location,
            description=description,
            employment_type=employment_type,
            remote_type=remote_type,
            profiles=profiles,
        )


def get_default_analyzer() -> JobAnalyzer:
    return RuleBasedJobAnalyzer()
