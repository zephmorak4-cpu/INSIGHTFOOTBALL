from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from .errors import MVPError
from .io_utils import now_iso


REQUIRED_FACT_GROUPS = {"fixture_identity", "recent_form", "team_news", "tournament_context", "verified_recent_news"}


def _source_fact(source: str, claim: str, status: str = "verified") -> dict[str, str]:
    return {"source": source, "fetched_at": now_iso(), "claim": claim, "verification_status": status}


def _get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def fetch_match_data(selection: dict[str, Any]) -> dict[str, Any]:
    """Fetch real selected-match data from configured APIs. No sample fallback is allowed."""
    if selection.get("selected_by") != "human_editor":
        raise MVPError("HUMAN_SELECTION_REQUIRED", "manual_match_input.json must be selected by a human editor.")

    facts: dict[str, list[dict[str, str]]] = {
        "fixture_identity": [],
        "recent_form": [],
        "goals": [],
        "team_news": [],
        "injuries_suspensions": [],
        "likely_lineups": [],
        "tactical_tendencies": [],
        "tournament_context": [],
        "head_to_head": [],
        "verified_recent_news": [],
    }
    sources: list[str] = []
    fixture_id = None

    football_key = os.environ.get("APP_FOOTBALL_API_KEY") or os.environ.get("API_FOOTBALL_API_KEY")
    if football_key:
        base = os.environ.get("FOOTBALL_API_BASE_URL", "https://v3.football.api-sports.io")
        headers = {"x-apisports-key": football_key, "Accept": "application/json"}
        query = urllib.parse.urlencode({"date": str(selection["kickoff_time"])[:10]})
        data = _get_json(f"{base.rstrip('/')}/fixtures?{query}", headers)
        for item in data.get("response", []):
            teams = item.get("teams", {})
            home = teams.get("home", {}).get("name", "")
            away = teams.get("away", {}).get("name", "")
            if {home.lower(), away.lower()} == {selection["home_team"].lower(), selection["away_team"].lower()}:
                fixture_id = item.get("fixture", {}).get("id")
                league = item.get("league", {}).get("name", selection["competition"])
                facts["fixture_identity"].append(_source_fact("API-Football fixtures", f"{home} vs {away} is listed in {league}."))
                facts["tournament_context"].append(_source_fact("API-Football fixtures", f"Stage/context: {selection.get('stage', 'selected match')} in {selection['competition']}."))
                break
        for team in [selection["home_team"], selection["away_team"]]:
            team_query = urllib.parse.urlencode({"search": team})
            teams_data = _get_json(f"{base.rstrip('/')}/teams?{team_query}", headers)
            response = teams_data.get("response", [])
            if response:
                team_id = response[0].get("team", {}).get("id")
                facts["fixture_identity"].append(_source_fact("API-Football teams", f"{team} team identity verified."))
                if team_id:
                    last = _recent_fixtures(base, headers, team_id)
                    played = last.get("response", [])
                    if played:
                        facts["recent_form"].append(_source_fact("API-Football recent fixtures", f"{team} recent form checked across {len(played)} recent fixture(s)."))
                        scored = conceded = 0
                        for match in played:
                            goals = match.get("goals", {})
                            is_home = match.get("teams", {}).get("home", {}).get("id") == team_id
                            scored += int(goals.get("home") or 0) if is_home else int(goals.get("away") or 0)
                            conceded += int(goals.get("away") or 0) if is_home else int(goals.get("home") or 0)
                        facts["goals"].append(_source_fact("API-Football recent fixtures", f"{team} scored {scored} and conceded {conceded} across the checked recent fixtures."))
        if fixture_id:
            events = _get_json(f"{base.rstrip('/')}/fixtures/lineups?fixture={fixture_id}", headers)
            if events.get("response"):
                facts["likely_lineups"].append(_source_fact("API-Football lineups", "Lineup data is available for the selected fixture."))
        sources.append("API-Football")

    gnews_key = os.environ.get("GNEWS_API_KEY")
    if gnews_key:
        query = urllib.parse.quote(f"{selection['home_team']} {selection['away_team']} {selection['competition']}")
        url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=5&apikey={urllib.parse.quote(gnews_key)}"
        news = _get_json(url)
        for article in news.get("articles", [])[:5]:
            title = article.get("title")
            source = article.get("source", {}).get("name", "GNews")
            if title:
                facts["verified_recent_news"].append(_source_fact(source, title))
        if facts["verified_recent_news"]:
            facts["team_news"].append(_source_fact("GNews", "Recent news coverage found for the selected match."))
        sources.append("GNews")

    if facts["goals"]:
        facts["tactical_tendencies"].append(_source_fact("Derived from verified recent fixtures", "Tactical notes must be based only on the checked form and news facts."))
    missing = sorted(group for group in REQUIRED_FACT_GROUPS if not facts[group])
    if missing:
        raise MVPError("INSUFFICIENT_REAL_MATCH_DATA", "Real match data is insufficient for production.", {"missing_groups": missing, "sources_checked": sources})

    return {"selection": selection, "fixture_id": fixture_id, "facts": facts, "sources": sources, "fetched_at": datetime.now(timezone.utc).isoformat()}


def _recent_fixtures(base: str, headers: dict[str, str], team_id: int) -> Any:
    restricted = _get_json(f"{base.rstrip('/')}/fixtures?team={team_id}&last=5", headers)
    if restricted.get("response"):
        return restricted
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=730)
    combined: list[dict[str, Any]] = []
    for season in [today.year, today.year - 1, today.year - 2]:
        query = urllib.parse.urlencode({"team": team_id, "season": season, "from": start.isoformat(), "to": today.isoformat()})
        window = _get_json(f"{base.rstrip('/')}/fixtures?{query}", headers)
        combined.extend(window.get("response", []))
        if len(combined) >= 5:
            break
    response = sorted(combined, key=lambda item: item.get("fixture", {}).get("date", ""), reverse=True)
    return {"response": response[:5], "results": len(response[:5])}
