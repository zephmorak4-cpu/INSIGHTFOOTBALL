from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "editorial-brain" / "output" / "live-daily-input.json"
DEFAULT_API_BASE = "https://v3.football.api-sports.io/fixtures"
HIGH_IMPORTANCE_COMPETITIONS = {
    "FIFA World Cup": 10,
    "UEFA Champions League": 10,
    "UEFA Europa League": 9,
    "Premier League": 9,
    "La Liga": 8,
    "Serie A": 8,
    "Bundesliga": 8,
    "Ligue 1": 7,
    "Africa Cup of Nations": 8,
    "UEFA European Championship": 10,
}
POPULAR_CLUBS = {
    "Arsenal",
    "Barcelona",
    "Bayern Munich",
    "Boca Juniors",
    "Chelsea",
    "Dynamo Kyiv",
    "Ferencvarosi TC",
    "HNK Hajduk Split",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Paris Saint Germain",
    "Qarabag",
    "Real Madrid",
    "Sheriff Tiraspol",
    "Tottenham",
}
COUNTRY_SPECIFIC_COMPETITIONS = {
    "Premier League": "England",
    "La Liga": "Spain",
    "Serie A": "Italy",
    "Bundesliga": "Germany",
    "Ligue 1": "France",
}


def build_live_daily_input(*, target_date: str | None = None, output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    production_date = target_date or datetime.now(ZoneInfo("Africa/Lagos")).date().isoformat()
    raw = fetch_fixtures(production_date)
    fixtures = normalize_fixtures(raw, production_date)
    if not fixtures:
        raise RuntimeError(f"No live fixtures returned for {production_date}. Production cannot use sample matches.")
    payload = {
        "production_metadata": {
            "date": production_date,
            "production_id": f"if-{production_date}-daily-live",
            "competition": "auto-selected",
            "match": "auto-selected",
            "kickoff_time": "auto-selected",
            "country": "auto-selected",
            "video_platform": "Telegram Approval",
            "language": "English",
            "producer": "INSIGHT FOOTBALL",
            "status": "production",
            "input_source": "live_football_api",
        },
        "fixtures": fixtures,
        "match_context": build_match_context(fixtures),
        "audience_notes": {"target": "general football fans", "region": "global"},
        "priority_competitions": list(HIGH_IMPORTANCE_COMPETITIONS),
        "data_availability_notes": {"source": "configured football API", "sample_matches_allowed": False},
    }
    editor_selection_path = os.environ.get("EDITOR_SELECTION_PATH")
    if editor_selection_path:
        payload = apply_editor_selection_file(payload, Path(editor_selection_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload


def apply_editor_selection_file(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    import sys

    module_path = ROOT / "editorial-brain" / "editor-match-selector" / "src"
    if str(module_path) not in sys.path:
        sys.path.insert(0, str(module_path))
    from editor_match_selector import apply_editor_selection, load_editor_selection

    return apply_editor_selection(payload, load_editor_selection(path))


def fetch_fixtures(production_date: str) -> Any:
    fixture_file = os.environ.get("INSIGHT_FOOTBALL_FIXTURES_FILE")
    if fixture_file:
        return json.loads(Path(fixture_file).read_text(encoding="utf-8"))
    api_key = os.environ.get("APP_FOOTBALL_API_KEY") or os.environ.get("API_FOOTBALL_API_KEY")
    if not api_key:
        raise RuntimeError("APP_FOOTBALL_API_KEY or API_FOOTBALL_API_KEY is required for production live fixture selection.")
    base = os.environ.get("FOOTBALL_API_BASE_URL", DEFAULT_API_BASE)
    separator = "&" if "?" in base else "?"
    url = base + separator + urllib.parse.urlencode({"date": production_date})
    request = urllib.request.Request(url, headers={"x-apisports-key": api_key, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_fixtures(raw: Any, production_date: str) -> list[dict[str, Any]]:
    items = raw.get("response", raw.get("fixtures", [])) if isinstance(raw, dict) else raw
    fixtures = []
    for item in items:
        fixture = _fixture_from_api_football(item, production_date) if isinstance(item, dict) else None
        if fixture:
            fixtures.append(fixture)
    return sorted(fixtures, key=_score_fixture, reverse=True)


def build_match_context(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    top_fixture = fixtures[0] if fixtures else {}
    home = str(top_fixture.get("home_team", "Home team"))
    away = str(top_fixture.get("away_team", "Away team"))
    return {
        "recent_form": {
            home: "Live fixture API selected this match as a high-interest fixture; verify latest form before publishing.",
            away: "Live fixture API selected this match as a high-interest fixture; verify latest form before publishing.",
            "summary": "Pre-match form context requires editorial verification from live sources.",
        },
        "squad_availability": {
            "confirmed_injuries": [],
            "suspensions": [],
            "fitness_concerns": [],
            "verification_required": True,
        },
        "tactical_notes": {
            "battle": "early pressure vs controlled buildup",
            "playing_style": "Use conservative broadcast analysis until team-specific notes are verified.",
            "verification_required": True,
        },
        "head_to_head": {
            "last_five_meetings": [],
            "historical_trends": "Verify before production narration.",
        },
        "statistics": {
            "available_data": "Fixture-level live API data available.",
            "first_half_theme": "Opening phase and early pressure should be checked against team form before publishing.",
            "verification_required": True,
        },
        "news": {
            "press_conference_notes": "Not supplied by fixture API.",
            "verification_required": True,
        },
        "betting_market_optional": {},
    }


def _fixture_from_api_football(item: dict[str, Any], production_date: str) -> dict[str, Any] | None:
    fixture_info = item.get("fixture", item)
    teams = item.get("teams", {})
    league = item.get("league", {})
    home = _name(teams.get("home")) or item.get("home_team")
    away = _name(teams.get("away")) or item.get("away_team")
    competition = league.get("name") or item.get("competition")
    kickoff = fixture_info.get("date") or item.get("kickoff_time")
    country = league.get("country") or item.get("country") or "Unknown"
    if not all([home, away, competition, kickoff]):
        return None
    if production_date not in str(kickoff):
        return None
    importance = _competition_importance(str(competition), str(country))
    audience = min(10, 4 + int(home in POPULAR_CLUBS) * 3 + int(away in POPULAR_CLUBS) * 3 + max(0, importance - 7))
    rivalry = 8 if home in POPULAR_CLUBS and away in POPULAR_CLUBS else 5
    story = min(10, round((audience + importance + rivalry) / 3))
    return {
        "home_team": str(home),
        "away_team": str(away),
        "competition": str(competition),
        "kickoff_time": str(kickoff),
        "country": str(country),
        "audience_interest": audience,
        "importance": importance,
        "rivalry": rivalry,
        "available_data": 8,
        "story_potential": story,
    }


def _name(value: Any) -> str:
    return str(value.get("name", "")) if isinstance(value, dict) else ""


def _competition_importance(competition: str, country: str) -> int:
    expected_country = COUNTRY_SPECIFIC_COMPETITIONS.get(competition)
    if expected_country and country != expected_country:
        return 5
    return HIGH_IMPORTANCE_COMPETITIONS.get(competition, 5)


def _score_fixture(fixture: dict[str, Any]) -> float:
    return (
        float(fixture.get("importance", 0)) * 2.0
        + float(fixture.get("audience_interest", 0)) * 2.0
        + float(fixture.get("rivalry", 0)) * 1.2
        + float(fixture.get("story_potential", 0)) * 2.6
        + float(fixture.get("available_data", 0)) * 2.2
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build today's live INSIGHT FOOTBALL Daily Input JSON.")
    parser.add_argument("--date")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    payload = build_live_daily_input(target_date=args.date, output_path=Path(args.output))
    print(json.dumps({"success": True, "output": args.output, "fixtures": len(payload["fixtures"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
