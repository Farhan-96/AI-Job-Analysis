"""Job source abstraction — adapters for permitted/approved input only."""

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
    posted_at: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)


def normalize_url_key(url: str) -> str:
    """Normalize a job URL for stable identity (no query/fragment)."""
    parsed = urlparse(url.strip())
    return f"{parsed.netloc}{parsed.path}".rstrip("/").lower()


def url_based_source_id(url: str) -> str:
    """Stable id when platform job id is unavailable."""
    digest = hashlib.sha256(normalize_url_key(url).encode("utf-8")).hexdigest()[:24]
    return f"url:{digest}"


class JobSource(ABC):
    """
    Abstract job source.

    Implementations must respect platform ToS / robots.txt.
    No CAPTCHA bypass, stealth scraping, or proxy rotation.
    """

    name: str

    def get_source_name(self) -> str:
        return self.name

    @abstractmethod
    def fetch_jobs(self) -> list[RawJob]:
        """Fetch jobs from the source (API/import/manual only — no auto-scrape)."""

    @abstractmethod
    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        """Validate and normalize a source-specific payload into RawJob."""

    def parse_job(self, payload: dict[str, Any]) -> RawJob:
        """Alias for normalize_job — kept for Phase 2 compatibility."""
        return self.normalize_job(payload)


def _resolve_source_job_id(
    payload: dict[str, Any],
    *,
    require_id_or_url: bool = False,
    fallback_prefix: str = "manual",
) -> str:
    source_job_id = payload.get("source_job_id")
    if source_job_id:
        return str(source_job_id).strip()

    url = payload.get("url")
    if url:
        return url_based_source_id(str(url))

    if require_id_or_url:
        raise ValueError("source_job_id or url is required")

    title = str(payload.get("title", "untitled"))
    company = str(payload.get("company") or "")
    digest = hashlib.sha256(f"{title}|{company}".encode()).hexdigest()[:24]
    return f"{fallback_prefix}:{digest}"


def _raw_from_payload(source: str, payload: dict[str, Any], source_job_id: str) -> RawJob:
    return RawJob(
        source=source,
        source_job_id=source_job_id,
        title=str(payload["title"]),
        company=payload.get("company"),
        location=payload.get("location"),
        url=payload.get("url"),
        description=str(payload.get("description") or ""),
        salary_min=_optional_float(payload.get("salary_min")),
        salary_max=_optional_float(payload.get("salary_max")),
        salary_currency=payload.get("salary_currency"),
        employment_type=payload.get("employment_type"),
        remote_type=payload.get("remote_type"),
        posted_at=str(payload["posted_at"]) if payload.get("posted_at") else None,
        raw_data=payload.get("raw_data") or dict(payload),
    )


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


class ManualJobSource(JobSource):
    """Jobs supplied manually via API / UI."""

    name = "manual"

    def fetch_jobs(self) -> list[RawJob]:
        return []

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        if not payload.get("title") or not str(payload.get("title")).strip():
            raise ValueError("title is required")
        source = str(payload.get("source") or self.name).strip().lower() or self.name
        source_job_id = _resolve_source_job_id(payload, fallback_prefix="manual")
        return _raw_from_payload(source, payload, source_job_id)


class IndeedJobSource(JobSource):
    """
    Indeed adapter for permitted/approved input methods.

    Supports: API payloads, CSV/JSON import, manually pasted jobs
    attributed to source='indeed'. Does NOT scrape or bypass anti-bot controls.
    """

    name = "indeed"

    def fetch_jobs(self) -> list[RawJob]:
        # No automatic collection — approved import paths only
        return []

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        if not payload.get("title") or not str(payload.get("title")).strip():
            raise ValueError("title is required")
        source_job_id = _resolve_source_job_id(payload, require_id_or_url=True)
        return _raw_from_payload(self.name, payload, source_job_id)


_META_SOURCES = frozenset({"csv", "json", "json_import", "api"})


def normalize_via_attributed_source(payload: dict[str, Any], default_source: str) -> RawJob:
    """
    Route a payload to the concrete adapter for its `source` field.

    Meta import channels (csv/json/api) fall through to ManualJobSource so the
    stored job.source reflects the attributed board (indeed, linkedin, …).
    """
    attributed = str(payload.get("source") or default_source).strip().lower() or default_source
    if attributed in _META_SOURCES:
        attributed = "manual"
        payload = {**payload, "source": attributed}

    if attributed == IndeedJobSource.name:
        return IndeedJobSource().normalize_job(payload)

    return ManualJobSource().normalize_job({**payload, "source": attributed})


class CsvImportJobSource(JobSource):
    """Normalize rows coming from CSV import (source column may override)."""

    name = "csv"

    def fetch_jobs(self) -> list[RawJob]:
        return []

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        return normalize_via_attributed_source(payload, default_source="manual")


class JsonImportJobSource(JobSource):
    """Import jobs from JSON payloads (permitted offline/import path)."""

    name = "json"

    def __init__(self, jobs: list[dict[str, Any]] | None = None) -> None:
        self._jobs = jobs or []

    def fetch_jobs(self) -> list[RawJob]:
        return [self.normalize_job(item) for item in self._jobs]

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        return normalize_via_attributed_source(payload, default_source="manual")


def get_source(name: str) -> JobSource:
    sources: dict[str, JobSource] = {
        ManualJobSource.name: ManualJobSource(),
        IndeedJobSource.name: IndeedJobSource(),
        CsvImportJobSource.name: CsvImportJobSource(),
        JsonImportJobSource.name: JsonImportJobSource(),
        "json_import": JsonImportJobSource(),  # Phase 2 alias
    }
    key = (name or "manual").strip().lower()
    if key not in sources:
        # Unknown boards (linkedin, company careers, …) use Manual with that name
        return ManualJobSource()
    return sources[key]
