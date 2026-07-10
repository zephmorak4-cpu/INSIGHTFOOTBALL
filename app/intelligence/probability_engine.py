from __future__ import annotations

from typing import Any


WEIGHTS = {"form": 0.45, "attack": 0.25, "defence": 0.2, "head_to_head": 0.1}


def calculate_probabilities(normalized: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    fixture = normalized["fixture"]
    recent = normalized.get("categories", {}).get("recent_form", {})
    home = recent.get(fixture["home_team"], {}).get("last_5", {}).get("value", {})
    away = recent.get(fixture["away_team"], {}).get("last_5", {}).get("value", {})
    home_score = _score(home)
    away_score = _score(away)
    draw_base = 26
    if validation["status"] != "SUFFICIENT":
        draw_base = 30
    total_strength = max(home_score + away_score, 1)
    remaining = 100 - draw_base
    home_prob = round(remaining * home_score / total_strength)
    away_prob = remaining - home_prob
    confidence = 0.78 if validation["status"] == "SUFFICIENT" else 0.45
    return {"team_a_win": home_prob, "draw": draw_base, "team_b_win": away_prob, "model_confidence": confidence, "data_quality": validation["status"], "factors": [{"name": key, "weight": value} for key, value in WEIGHTS.items()], "limitations": validation.get("warnings", []) + validation.get("missing_categories", [])}


def _score(form: dict[str, Any]) -> float:
    if not form:
        return 1
    return 1 + form.get("wins", 0) * 3 + form.get("draws", 0) + form.get("goals_scored", 0) * 0.25 - form.get("goals_conceded", 0) * 0.2 + form.get("clean_sheets", 0) * 0.5
