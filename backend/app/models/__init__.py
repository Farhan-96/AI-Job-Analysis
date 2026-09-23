"""Model exports for Alembic metadata discovery."""

from app.models.health import HealthCheck
from app.models.import_history import JobImport, JobSourceConfig
from app.models.job import Job, JobSkill
from app.models.match import JobProfileMatch
from app.models.profile import ProfileSkill, ResumeProfile

__all__ = [
    "HealthCheck",
    "Job",
    "JobSkill",
    "JobImport",
    "JobSourceConfig",
    "JobProfileMatch",
    "ProfileSkill",
    "ResumeProfile",
]
