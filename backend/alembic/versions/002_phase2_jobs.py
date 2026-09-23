"""Phase 2 schema: resume profiles, jobs, skills, and profile matches.

Revision ID: 002_phase2_jobs
Revises: 001_phase1_health
Create Date: 2026-03-23 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_phase2_jobs"
down_revision: str | None = "001_phase1_health"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resume_file", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "title_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "preferred_locations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("remote_ok", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("min_experience_years", sa.Float(), nullable=True),
        sa.Column("max_experience_years", sa.Float(), nullable=True),
        sa.Column(
            "education_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("match_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_resume_profiles_slug", "resume_profiles", ["slug"])

    op.create_table(
        "profile_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=128), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="5"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["profile_id"], ["resume_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profile_skills_profile_id", "profile_skills", ["profile_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_job_id", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("remote_type", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("salary_min", sa.Float(), nullable=True),
        sa.Column("salary_max", sa.Float(), nullable=True),
        sa.Column("salary_currency", sa.String(length=16), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("extracted_experience_years", sa.Float(), nullable=True),
        sa.Column("extracted_education", sa.String(length=255), nullable=True),
        sa.Column("normalized_title", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_job_id", name="uq_jobs_source_source_job_id"),
    )
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_source_job_id", "jobs", ["source_job_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "job_skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=128), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="dictionary"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_skills_job_id", "job_skills", ["job_id"])

    op.create_table(
        "job_profile_matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column(
            "matching_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "missing_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "matching_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "missing_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("experience_match", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("education_match", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("role_match", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("location_match", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("salary_match", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("analysis", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommendation", sa.String(length=64), nullable=False, server_default="review"),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["resume_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "profile_id", name="uq_job_profile_matches_job_profile"),
    )
    op.create_index("ix_job_profile_matches_job_id", "job_profile_matches", ["job_id"])
    op.create_index("ix_job_profile_matches_profile_id", "job_profile_matches", ["profile_id"])


def downgrade() -> None:
    op.drop_table("job_profile_matches")
    op.drop_table("job_skills")
    op.drop_table("jobs")
    op.drop_table("profile_skills")
    op.drop_table("resume_profiles")
