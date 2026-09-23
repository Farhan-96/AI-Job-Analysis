"""Resume profile API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import profile_repository
from app.schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate
from app.services import profile_service

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileOut])
def list_profiles(db: Session = Depends(get_db)) -> list[ProfileOut]:
    return [
        ProfileOut.model_validate(p) for p in profile_repository.list_profiles(db)
    ]


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> ProfileOut:
    profile = profile_repository.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)) -> ProfileOut:
    profile = profile_service.create_profile(db, payload)
    return ProfileOut.model_validate(profile)


@router.put("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = profile_service.update_profile(db, profile_id, payload)
    return ProfileOut.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: int, db: Session = Depends(get_db)) -> None:
    profile_service.delete_profile(db, profile_id)
