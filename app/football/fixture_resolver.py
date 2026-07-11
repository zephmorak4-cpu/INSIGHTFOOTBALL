from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import Settings
from app.models.football_models import Fixture
from app.models.output_models import AppError
from app.models.request_models import MatchRequest


ALIASES = {"man city": "manchester city", "man utd": "manchester united", "psg": "paris saint germain"}


def resolve_fixture(request: MatchRequest, settings: Settings, run_id: str) -> Fixture:
    if not settings.football_api_key:
        raise AppError("FOOTBALL_API_UNAVAILABLE", "fixture_resolver", "Football API key is not configured.", True, run_id)
    today = datetime.now(timezone.utc).date()
    candidates: list[dict[str, Any]] = []
    for offset in [0, 30, 90, 180, 365]:
        start = today.isoformat()
        end = (today + timedelta(days=offset or 7)).isoformat()
        query = urllib.parse.urlencode({"from": start, "to": end})
        data = _api_get(f"{settings.football_api_base_url.rstrip('/')}/fixtures?{query}", settings)
        candidates.extend(data.get("response", []))
        matches = [_fixture for _fixture in candidates if _matches(_fixture, request)]
        if matches:
            matches = sorted(matches, key=lambda item: item.get("fixture", {}).get("date", ""))
            unique = {_identity(item): item for item in matches}
            if len(unique) > 1 and _same_day_conflict(list(unique.values())):
                raise AppError("AMBIGUOUS_FIXTURE", "fixture_resolver", "Several plausible fixtures matched. Please clarify the competition or date.", False, run_id)
            return _to_fixture(list(unique.values())[0])
    raise AppError("FIXTURE_NOT_FOUND", "fixture_resolver", "No upcoming fixture matched both teams and competition.", False, run_id)


def _api_get(url: str, settings: Settings) -> dict[str, Any]:
    headers = {"x-apisports-key": settings.football_api_key, "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _norm(value: str) -> str:
    text = value.lower().replace("-", " ").strip()
    for noise in ["quarter final", "quarter-final", "semifinal", "semi final", "final", "round of 16", "group stage"]:
        text = text.replace(noise, "").strip()
    text = " ".join(text.split())
    if text == "world cup":
        text = "fifa world cup"
    return ALIASES.get(text, text)


def _matches(item: dict[str, Any], request: MatchRequest) -> bool:
    teams = item.get("teams", {})
    league = item.get("league", {})
    home = _norm(teams.get("home", {}).get("name", ""))
    away = _norm(teams.get("away", {}).get("name", ""))
    requested = {_norm(request.home_team), _norm(request.away_team)}
    actual = {home, away}
    competition = _norm(league.get("name", ""))
    requested_competition = _norm(request.competition)
    return requested == actual and (requested_competition in competition or competition in requested_competition)


def _identity(item: dict[str, Any]) -> str:
    return str(item.get("fixture", {}).get("id") or item.get("fixture", {}).get("date"))


def _same_day_conflict(items: list[dict[str, Any]]) -> bool:
    days = {str(item.get("fixture", {}).get("date", ""))[:10] for item in items}
    return len(days) == 1


def _to_fixture(item: dict[str, Any]) -> Fixture:
    fixture = item.get("fixture", {})
    teams = item.get("teams", {})
    league = item.get("league", {})
    venue = fixture.get("venue") or {}
    return Fixture(
        fixture_id=str(fixture.get("id", "")),
        home_team=teams.get("home", {}).get("name", ""),
        away_team=teams.get("away", {}).get("name", ""),
        competition=league.get("name", ""),
        kickoff_time=fixture.get("date", ""),
        venue=venue.get("name"),
        status=fixture.get("status", {}).get("short", ""),
        source="API-Football",
    )
