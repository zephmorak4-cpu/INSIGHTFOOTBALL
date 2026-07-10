from __future__ import annotations

from typing import Any


def discover_insight(normalized: dict[str, Any], report: str) -> dict[str, Any]:
    fixture = normalized["fixture"]
    recent = normalized.get("categories", {}).get("recent_form", {})
    home = recent.get(fixture["home_team"], {}).get("last_5", {}).get("value", {})
    away = recent.get(fixture["away_team"], {}).get("last_5", {}).get("value", {})
    home_goal_gap = home.get("goals_scored", 0) - home.get("goals_conceded", 0)
    away_goal_gap = away.get("goals_scored", 0) - away.get("goals_conceded", 0)
    if home_goal_gap >= away_goal_gap:
        central = f"{fixture['home_team']}'s recent balance between scoring and defending looks like the clearest pressure point."
        watch = f"Watch whether {fixture['away_team']} can disturb that balance early without overcommitting."
    else:
        central = f"{fixture['away_team']}'s recent goal balance may be the detail that changes how this match feels."
        watch = f"Watch whether {fixture['home_team']} can control the game before that away threat grows."
    support = [
        {"claim": f"{fixture['home_team']} recent goal difference in checked matches: {home_goal_gap}.", "source": "API-Football", "confidence": 0.75},
        {"claim": f"{fixture['away_team']} recent goal difference in checked matches: {away_goal_gap}.", "source": "API-Football", "confidence": 0.75},
    ]
    return {"central_insight": central, "audience_assumption": "Most fans focus on the bigger name or headline players.", "surprising_reversal": "The stronger clue may be the recent balance between chance creation and defensive control.", "supporting_evidence": support, "counter_evidence": [{"claim": "Recent form does not guarantee performance in a one-off fixture.", "source": "Model limitation", "confidence": 0.65}], "why_it_matters": "It frames what each team must protect before chasing the match.", "what_to_watch": watch, "confidence": 0.72}
