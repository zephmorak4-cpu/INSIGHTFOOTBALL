from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.request_models import MatchRequest


def validate_data(request: MatchRequest, normalized: dict[str, Any]) -> dict[str, Any]:
    fixture = normalized.get("fixture", {})
    warnings: list[str] = []
    available: list[str] = []
    missing: list[str] = []
    if {fixture.get("home_team", "").lower(), fixture.get("away_team", "").lower()} != {request.home_team.lower(), request.away_team.lower()}:
        warnings.append("Fixture teams do not match request.")
    if request.competition.lower() not in fixture.get("competition", "").lower():
        warnings.append("Fixture competition does not match request.")
    try:
        kickoff = datetime.fromisoformat(str(fixture.get("kickoff_time", "")).replace("Z", "+00:00"))
        if kickoff < datetime.now(timezone.utc):
            warnings.append("Fixture is not upcoming.")
    except ValueError:
        warnings.append("Kickoff time is invalid.")
    categories = normalized.get("categories", {})
    for category in ["match_context", "recent_form", "head_to_head", "news"]:
        if categories.get(category):
            available.append(category)
        else:
            missing.append(category)
    recent = categories.get("recent_form", {})
    if len(recent) < 2:
        missing.append("both_teams_recent_form")
    status = "SUFFICIENT" if not warnings and "both_teams_recent_form" not in missing else "PARTIAL" if available else "INSUFFICIENT"
    return {"status": status, "available_categories": sorted(set(available)), "missing_categories": sorted(set(missing)), "warnings": warnings}
