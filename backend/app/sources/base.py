"""Job source abstraction — adapters for permitted/approved input only."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse
import hashlib
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


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


@dataclass
class SearchCriteria:
    """Normalized search inputs passed to JobSource.search()."""

    keywords: list[str]
    locations: list[str]
    remote_types: list[str]
    max_jobs: int = 50
    profile_slug: str | None = None
    profile_name: str | None = None


class SearchableProfile(Protocol):
    """Minimal profile shape accepted by search()."""

    keywords: list[Any] | Any
    locations: list[Any] | Any
    remote_types: list[Any] | Any
    slug: str
    name: str


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

    def search(self, search_profile: SearchableProfile | SearchCriteria) -> list[RawJob]:
        """
        Discover jobs for a search profile.

        Default: not supported. Override in adapters that can safely search.
        """
        raise NotImplementedError(
            f"Source '{self.get_source_name()}' does not support automated search"
        )


def _criteria_from_profile(
    search_profile: SearchableProfile | SearchCriteria,
    *,
    max_jobs: int | None = None,
) -> SearchCriteria:
    if isinstance(search_profile, SearchCriteria):
        if max_jobs is not None:
            return SearchCriteria(
                keywords=search_profile.keywords,
                locations=search_profile.locations,
                remote_types=search_profile.remote_types,
                max_jobs=max_jobs,
                profile_slug=search_profile.profile_slug,
                profile_name=search_profile.profile_name,
            )
        return search_profile

    keywords = [str(k).strip() for k in (search_profile.keywords or []) if str(k).strip()]
    locations = [
        str(loc).strip() for loc in (search_profile.locations or []) if str(loc).strip()
    ]
    remote_types = [
        str(rt).strip().lower()
        for rt in (search_profile.remote_types or [])
        if str(rt).strip()
    ]
    return SearchCriteria(
        keywords=keywords,
        locations=locations,
        remote_types=remote_types,
        max_jobs=max_jobs or 50,
        profile_slug=getattr(search_profile, "slug", None),
        profile_name=getattr(search_profile, "name", None),
    )


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


def _text_blob(*parts: Any) -> str:
    return " ".join(str(p or "").lower() for p in parts)


def _matches_criteria(payload: dict[str, Any], criteria: SearchCriteria) -> bool:
    blob = _text_blob(
        payload.get("title"),
        payload.get("description"),
        payload.get("company"),
        " ".join(payload.get("tags") or []),
    )
    if criteria.keywords:
        if not any(kw.lower() in blob for kw in criteria.keywords):
            return False

    if criteria.locations:
        loc = str(payload.get("location") or "").lower()
        remote = str(payload.get("remote_type") or "").lower()
        location_hit = any(
            loc_kw.lower() in loc or loc_kw.lower() == "remote" and remote == "remote"
            for loc_kw in criteria.locations
        )
        if not location_hit:
            # Allow Pakistan-wide / Remote flexible matches when location is Remote
            if remote == "remote" and any(
                loc_kw.lower() in {"remote", "pakistan"} for loc_kw in criteria.locations
            ):
                pass
            else:
                return False

    if criteria.remote_types:
        remote = str(payload.get("remote_type") or "unknown").lower()
        if remote not in {rt.lower() for rt in criteria.remote_types}:
            return False

    return True


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

    def search(self, search_profile: SearchableProfile | SearchCriteria) -> list[RawJob]:
        raise NotImplementedError(
            "Manual source does not support automated search — use mock or an "
            "approved feed-backed source"
        )


class IndeedJobSource(JobSource):
    """
    Indeed adapter for permitted/approved input methods.

    Supports:
    - API / CSV / JSON / pasted payloads attributed to source='indeed'
    - Optional approved feed file/URL via INDEED_APPROVED_FEED_PATH or
      INDEED_APPROVED_FEED_URL (HTTP GET of a JSON feed you control)

    Does NOT scrape Indeed HTML, bypass CAPTCHA, rotate proxies, spoof
    fingerprints, or automate login.
    """

    name = "indeed"

    def fetch_jobs(self) -> list[RawJob]:
        # No automatic HTML collection — approved import / feed paths only
        return []

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        if not payload.get("title") or not str(payload.get("title")).strip():
            raise ValueError("title is required")
        source_job_id = _resolve_source_job_id(payload, require_id_or_url=True)
        return _raw_from_payload(self.name, payload, source_job_id)

    def search(self, search_profile: SearchableProfile | SearchCriteria) -> list[RawJob]:
        criteria = _criteria_from_profile(search_profile)
        feed_jobs = self._load_approved_feed()
        if feed_jobs is None:
            raise RuntimeError(
                "source unavailable — configure INDEED_APPROVED_FEED_PATH or "
                "INDEED_APPROVED_FEED_URL with a permitted JSON feed, or import "
                "jobs via CSV/JSON/manual. HTML scraping is not supported."
            )

        matched: list[RawJob] = []
        for item in feed_jobs:
            if not isinstance(item, dict):
                continue
            if not _matches_criteria(item, criteria):
                continue
            try:
                matched.append(self.normalize_job({**item, "source": self.name}))
            except ValueError:
                continue
            if len(matched) >= criteria.max_jobs:
                break
        return matched

    def _load_approved_feed(self) -> list[dict[str, Any]] | None:
        """Load jobs from an operator-supplied approved feed (file or URL)."""
        path = os.environ.get("INDEED_APPROVED_FEED_PATH", "").strip()
        if path:
            feed_path = Path(path)
            if not feed_path.is_file():
                logger.warning("Indeed approved feed path not found")
                return None
            try:
                data = json.loads(feed_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Indeed approved feed unreadable: %s", type(exc).__name__)
                return None
            return self._extract_jobs_list(data)

        url = os.environ.get("INDEED_APPROVED_FEED_URL", "").strip()
        if url:
            try:
                import urllib.request

                with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310
                    data = json.loads(response.read().decode("utf-8"))
                return self._extract_jobs_list(data)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Indeed approved feed URL unavailable: %s", type(exc).__name__
                )
                return None

        return None

    @staticmethod
    def _extract_jobs_list(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and isinstance(data.get("jobs"), list):
            return [item for item in data["jobs"] if isinstance(item, dict)]
        return []


class MockJobSource(JobSource):
    """
    Development/mock source — clearly marked source='mock'.

    Does not call external websites. Jobs are tagged as mock data.
    """

    name = "mock"

    def fetch_jobs(self) -> list[RawJob]:
        from app.sources.mock_catalog import MOCK_JOB_CATALOG

        return [self.normalize_job(item) for item in MOCK_JOB_CATALOG]

    def normalize_job(self, payload: dict[str, Any]) -> RawJob:
        if not payload.get("title") or not str(payload.get("title")).strip():
            raise ValueError("title is required")
        source_job_id = _resolve_source_job_id(payload, fallback_prefix="mock")
        raw = _raw_from_payload(self.name, payload, source_job_id)
        # Ensure mock attribution is preserved in raw_data
        meta = dict(raw.raw_data or {})
        meta["is_mock"] = True
        meta["mock_notice"] = "MOCK DATA — not a real job"
        raw.raw_data = meta
        return raw

    def search(self, search_profile: SearchableProfile | SearchCriteria) -> list[RawJob]:
        from app.sources.mock_catalog import MOCK_JOB_CATALOG

        criteria = _criteria_from_profile(search_profile)
        matched: list[RawJob] = []
        for item in MOCK_JOB_CATALOG:
            if not _matches_criteria(item, criteria):
                continue
            matched.append(self.normalize_job(item))
            if len(matched) >= criteria.max_jobs:
                break
        return matched


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
    if attributed == MockJobSource.name:
        return MockJobSource().normalize_job(payload)

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
        MockJobSource.name: MockJobSource(),
        CsvImportJobSource.name: CsvImportJobSource(),
        JsonImportJobSource.name: JsonImportJobSource(),
        "json_import": JsonImportJobSource(),  # Phase 2 alias
    }
    key = (name or "manual").strip().lower()
    if key not in sources:
        # Unknown boards (linkedin, company careers, …) use Manual with that name
        return ManualJobSource()
    return sources[key]
