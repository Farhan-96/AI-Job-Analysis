"""Job source abstraction — Indeed adapter is first; no scraping bypass."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse
import hashlib


@dataclass
class RawJob:
    source: str
    source_job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    url: str | None = None
    description: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    employment_type: str | None = None
    remote_type: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


def url_based_source_id(url: str) -> str:
    """Stable id when platform job id is unavailable."""
    parsed = urlparse(url.strip())
    normalized = f"{parsed.netloc}{parsed.path}".rstrip("/").lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
    return f"url:{digest}"


class JobSource(ABC):
    """Abstract job source. Implementations must respect ToS / robots.txt."""

    name: str

    @abstractmethod
    def fetch_jobs(self) -> list[RawJob]:
        """Fetch jobs from the source (API/import/manual only in Phase 2)."""

    @abstractmethod
    def parse_job(self, payload: dict[str, Any]) -> RawJob:
        """Parse a source-specific payload into RawJob."""

    def normalize_job(self, job: RawJob) -> RawJob:
        """Optional source-specific normalization hook."""
        return job


class ManualJobSource(JobSource):
    """Jobs supplied manually via API / UI."""

    name = "manual"

    def fetch_jobs(self) -> list[RawJob]:
        return []

    def parse_job(self, payload: dict[str, Any]) -> RawJob:
        url = payload.get("url")
        source_job_id = payload.get("source_job_id")
        if not source_job_id:
            if url:
                source_job_id = url_based_source_id(str(url))
            else:
                title = str(payload.get("title", "untitled"))
                company = str(payload.get("company") or "")
                digest = hashlib.sha256(f"{title}|{company}".encode()).hexdigest()[:24]
                source_job_id = f"manual:{digest}"

        return RawJob(
            source=str(payload.get("source") or self.name),
            source_job_id=str(source_job_id),
            title=str(payload["title"]),
            company=payload.get("company"),
            location=payload.get("location"),
            url=url,
            description=str(payload.get("description") or ""),
            salary_min=payload.get("salary_min"),
            salary_max=payload.get("salary_max"),
            salary_currency=payload.get("salary_currency"),
            employment_type=payload.get("employment_type"),
            remote_type=payload.get("remote_type"),
            raw_data=payload.get("raw_data") or payload,
        )


class IndeedJobSource(JobSource):
    """
    Indeed adapter scaffold.

    Phase 2 does NOT scrape Indeed or bypass anti-bot controls.
    Jobs can be supplied via approved API payloads, JSON/CSV import,
    or manually pasted descriptions attributed to source='indeed'.
    """

    name = "indeed"

    def fetch_jobs(self) -> list[RawJob]:
        # No automatic collection in Phase 2
        return []

    def parse_job(self, payload: dict[str, Any]) -> RawJob:
        url = payload.get("url")
        source_job_id = payload.get("source_job_id")
        if not source_job_id and url:
            source_job_id = url_based_source_id(str(url))
        if not source_job_id:
            raise ValueError("Indeed jobs require source_job_id or url")

        return RawJob(
            source=self.name,
            source_job_id=str(source_job_id),
            title=str(payload["title"]),
            company=payload.get("company"),
            location=payload.get("location"),
            url=url,
            description=str(payload.get("description") or ""),
            salary_min=payload.get("salary_min"),
            salary_max=payload.get("salary_max"),
            salary_currency=payload.get("salary_currency"),
            employment_type=payload.get("employment_type"),
            remote_type=payload.get("remote_type"),
            raw_data=payload,
        )


class JsonImportJobSource(JobSource):
    """Import jobs from JSON payloads (permitted offline/import path)."""

    name = "json_import"

    def __init__(self, jobs: list[dict[str, Any]] | None = None) -> None:
        self._jobs = jobs or []

    def fetch_jobs(self) -> list[RawJob]:
        return [self.parse_job(item) for item in self._jobs]

    def parse_job(self, payload: dict[str, Any]) -> RawJob:
        manual = ManualJobSource()
        job = manual.parse_job(payload)
        job.source = self.name
        return job


def get_source(name: str) -> JobSource:
    sources: dict[str, JobSource] = {
        ManualJobSource.name: ManualJobSource(),
        IndeedJobSource.name: IndeedJobSource(),
        JsonImportJobSource.name: JsonImportJobSource(),
    }
    if name not in sources:
        return ManualJobSource()
    return sources[name]
