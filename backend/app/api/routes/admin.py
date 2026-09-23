"""Admin / development utility routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.seed import run_seed

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/seed")
def seed_development_data(db: Session = Depends(get_db)) -> dict[str, int]:
    """Populate default profiles and clearly marked development sample jobs."""
    return run_seed(db)
