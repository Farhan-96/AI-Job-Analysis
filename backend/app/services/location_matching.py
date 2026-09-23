"""Location / remote matching against profile preferences."""

from __future__ import annotations

from app.models.enums import RemoteType


def compare_location(
    *,
    remote_type: str,
    location: str | None,
    preferred_locations: list[str],
    remote_ok: bool,
) -> str:
    """
    Return true|false|unknown for location fit.

    Remote jobs match when the profile allows remote.
    On-site jobs match when the city is in preferred_locations.
    """
    preferred_lower = [p.lower() for p in preferred_locations]

    if remote_type == RemoteType.REMOTE.value:
        return "true" if remote_ok else "false"

    if remote_type == RemoteType.HYBRID.value:
        if remote_ok:
            return "true"
        if location and any(p in location.lower() for p in preferred_lower):
            return "true"
        if preferred_locations:
            return "false"
        return "unknown"

    if remote_type == RemoteType.ONSITE.value:
        if not location:
            return "unknown"
        if any(p in location.lower() for p in preferred_lower):
            return "true"
        if preferred_locations:
            return "false"
        return "unknown"

    # unknown remote type
    if location and preferred_lower and any(p in location.lower() for p in preferred_lower):
        return "true"
    return "unknown"
