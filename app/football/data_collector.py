from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import Settings
from app.models.football_models import DataItem, Fixture, MatchData
from app.models.output_models import AppError


def collect_match_data(fixture: Fixture, settings: Settings, run_id: str) -> MatchData:
    categories: dict[str, Any] = {
        "match_context": {"fixture": _item(fixture.fixture_id, fixture.source, 1.0), "venue": _item(fixture.venue, fixture.source, 0.8)},
        "recent_form": {},
        "head_to_head": {"items": []},
        "tactical_profile": {},
        "squad_context": {},
        "player_form": {},
        "news": [],
    }
    sources = [fixture.source]
    if not settings.football_api_key:
        raise AppError("FOOTBALL_API_UNAVAILABLE", "data_collector", "Football API key is not configured.", True, run_id)
    for team in [fixture.home_team, fixture.away_team]:
        team_id = _team_id(team, settings)
        if team_id:
            recent = _recent(team_id, settings)
            categories["recent_form"][team] = _summarize_form(team, team_id, recent)
    h2h = _api_get(f"{settings.football_api_base_url.rstrip('/')}/fixtures/headtohead?h2h={urllib.parse.quote(_h2h_ids(fixture, settings))}", settings)
    categories["head_to_head"]["items"] = h2h.get("response", [])[:10]
    if settings.gnews_api_key:
        categories["news"] = _news(fixture, settings)
        if categories["news"]:
            sources.append("GNews")
    return MatchData(fixture=fixture, categories=categories, sources=sources)


def _item(value: Any, source: str, confidence: float) -> dict[str, Any]:
    return {"value": value, "source": source, "fetched_at": datetime.now(timezone.utc).isoformat(), "verified": value is not None, "confidence": confidence}


def _api_get(url: str, settings: Settings) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"x-apisports-key": settings.football_api_key, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _team_id(team: str, settings: Settings) -> int | None:
    data = _api_get(f"{settings.football_api_base_url.rstrip('/')}/teams?{urllib.parse.urlencode({'search': team})}", settings)
    for item in data.get("response", []):
        if item.get("team", {}).get("name", "").lower() == team.lower():
            return item.get("team", {}).get("id")
    return data.get("response", [{}])[0].get("team", {}).get("id") if data.get("response") else None


def _recent(team_id: int, settings: Settings) -> list[dict[str, Any]]:
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=730)
    combined: list[dict[str, Any]] = []
    for season in [today.year, today.year - 1, today.year - 2]:
        query = urllib.parse.urlencode({"team": team_id, "season": season, "from": start.isoformat(), "to": today.isoformat()})
        data = _api_get(f"{settings.football_api_base_url.rstrip('/')}/fixtures?{query}", settings)
        combined.extend(data.get("response", []))
    return sorted(combined, key=lambda item: item.get("fixture", {}).get("date", ""), reverse=True)[:10]


def _summarize_form(team: str, team_id: int, matches: list[dict[str, Any]]) -> dict[str, Any]:
    wins = draws = losses = scored = conceded = clean_sheets = 0
    for item in matches[:5]:
        goals = item.get("goals", {})
        home_id = item.get("teams", {}).get("home", {}).get("id")
        own = goals.get("home") if home_id == team_id else goals.get("away")
        opp = goals.get("away") if home_id == team_id else goals.get("home")
        if own is None or opp is None:
            continue
        scored += own
        conceded += opp
        clean_sheets += int(opp == 0)
        wins += int(own > opp)
        draws += int(own == opp)
        losses += int(own < opp)
    return {"last_5": _item({"wins": wins, "draws": draws, "losses": losses, "goals_scored": scored, "goals_conceded": conceded, "clean_sheets": clean_sheets, "matches_checked": len(matches[:5])}, "API-Football", 0.85)}


def _h2h_ids(fixture: Fixture, settings: Settings) -> str:
    home = _team_id(fixture.home_team, settings)
    away = _team_id(fixture.away_team, settings)
    return f"{home}-{away}" if home and away else "0-0"


def _news(fixture: Fixture, settings: Settings) -> list[dict[str, Any]]:
    query = urllib.parse.quote(f"{fixture.home_team} {fixture.away_team} {fixture.competition}")
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=5&apikey={urllib.parse.quote(settings.gnews_api_key)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    return [_item(article.get("title"), article.get("source", {}).get("name", "GNews"), 0.75) for article in data.get("articles", []) if article.get("title")]
