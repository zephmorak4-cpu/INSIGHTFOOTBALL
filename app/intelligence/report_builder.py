from __future__ import annotations

from typing import Any


def build_report(normalized: dict[str, Any], validation: dict[str, Any]) -> str:
    fixture = normalized["fixture"]
    recent = normalized.get("categories", {}).get("recent_form", {})
    news = normalized.get("categories", {}).get("news", [])
    sections = [
        "# Football Intelligence Report",
        "## 1. Match Overview",
        f"{fixture['home_team']} vs {fixture['away_team']} in {fixture['competition']}. Kickoff: {fixture['kickoff_time']}. Venue: {fixture.get('venue') or 'Unavailable'}.",
        "## 2. Team A - Last Five Form",
        _form_text(fixture["home_team"], recent.get(fixture["home_team"], {})),
        "## 3. Team B - Last Five Form",
        _form_text(fixture["away_team"], recent.get(fixture["away_team"], {})),
        "## 4. Head-to-Head",
        "Head-to-head data is included where the provider returned verified records.",
        "## 5. Home and Away Context",
        f"{fixture['home_team']} is listed as home team; {fixture['away_team']} is listed as away team.",
        "## 6. Attacking Trends",
        _trend(fixture["home_team"], recent.get(fixture["home_team"], {}), "goals_scored"),
        _trend(fixture["away_team"], recent.get(fixture["away_team"], {}), "goals_scored"),
        "## 7. Defensive Trends",
        _trend(fixture["home_team"], recent.get(fixture["home_team"], {}), "goals_conceded"),
        _trend(fixture["away_team"], recent.get(fixture["away_team"], {}), "goals_conceded"),
        "## 8. Tactical Tendencies",
        "Tactical tendencies are limited to patterns supported by available form, goals, and news data.",
        "## 9. Squad Availability",
        "Unavailable from current providers unless listed in verified news.",
        "## 10. Players to Watch",
        "Unavailable from current providers unless listed in verified news.",
        "## 11. Historical Patterns",
        "Use provider head-to-head records where available.",
        "## 12. Hidden Match Patterns",
        "Hidden patterns should be treated cautiously when data sufficiency is partial.",
        "## 13. Contradicting Evidence",
        "Contradictions are noted in insight discovery when available.",
        "## 14. Overall Data Summary",
        f"Data sufficiency: {validation['status']}. Missing: {', '.join(validation.get('missing_categories', [])) or 'none'}.",
        "## 15. Sources Used",
        "\n".join(f"- {source}" for source in normalized.get("sources", [])),
    ]
    if news:
        sections.extend(["## Verified Recent News", *[f"- {item['value']} ({item['source']})" for item in news[:5]]])
    return "\n\n".join(sections)


def _form_text(team: str, data: dict[str, Any]) -> str:
    value = data.get("last_5", {}).get("value")
    if not value:
        return f"No sufficient recent form returned for {team}."
    return f"{team}: {value['wins']}W {value['draws']}D {value['losses']}L, {value['goals_scored']} scored, {value['goals_conceded']} conceded, {value['clean_sheets']} clean sheets."


def _trend(team: str, data: dict[str, Any], key: str) -> str:
    value = data.get("last_5", {}).get("value")
    return f"{team}: {value.get(key)} in checked recent matches." if value else f"{team}: unavailable."
