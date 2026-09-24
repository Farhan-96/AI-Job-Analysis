"""Phase 3 Step 2: job search profiles and search runs.

Revision ID: 004_phase3_search
Revises: 003_phase3_import
Create Date: 2026-09-23 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_phase3_search"
down_revision: str | None = "003_phase3_import"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_search_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("locations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("remote_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="mock"),
        sa.Column(
            "schedule_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "schedule_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resume_profile_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["resume_profile_id"],
            ["resume_profiles.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        "ix_job_search_profiles_slug", "job_search_profiles", ["slug"]
    )
    op.create_index(
        "ix_job_search_profiles_resume_profile_id",
        "job_search_profiles",
        ["resume_profile_id"],
    )

    op.create_table(
        "job_search_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("search_profile_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="running",
        ),
        sa.Column("jobs_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_imported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["search_profile_id"],
            ["job_search_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_job_search_runs_search_profile_id",
        "job_search_runs",
        ["search_profile_id"],
    )
    op.create_index("ix_job_search_runs_status", "job_search_runs", ["status"])

    op.add_column(
        "jobs",
        sa.Column("search_profile_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_jobs_search_profile_id", "jobs", ["search_profile_id"])
    op.create_foreign_key(
        "fk_jobs_search_profile_id",
        "jobs",
        "job_search_profiles",
        ["search_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_jobs_search_profile_id", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_search_profile_id", table_name="jobs")
    op.drop_column("jobs", "search_profile_id")

    op.drop_index("ix_job_search_runs_status", table_name="job_search_runs")
    op.drop_index(
        "ix_job_search_runs_search_profile_id", table_name="job_search_runs"
    )
    op.drop_table("job_search_runs")

    op.drop_index(
        "ix_job_search_profiles_resume_profile_id",
        table_name="job_search_profiles",
    )
    op.drop_index("ix_job_search_profiles_slug", table_name="job_search_profiles")
    op.drop_table("job_search_profiles")
