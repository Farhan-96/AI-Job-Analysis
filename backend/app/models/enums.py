"""Shared enums and constants for Phase 2 models."""

from enum import StrEnum


class JobStatus(StrEnum):
    NEW = "new"
    ANALYZED = "analyzed"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    APPLIED = "applied"


class RemoteType(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class MatchLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"
    TRUE = "true"
    FALSE = "false"


class SearchRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
