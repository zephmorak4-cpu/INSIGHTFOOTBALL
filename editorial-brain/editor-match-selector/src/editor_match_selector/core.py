from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "production_id",
    "production_date",
    "selected_match",
    "home_team",
    "away_team",
    "competition",
    "kickoff_time",
    "match_priority",
    "editor_notes",
]


def load_editor_selection(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Editor selection must be a JSON object.")
    validate_editor_selection(data)
    return data


def validate_editor_selection(selection: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(selection.get(field, "")).strip()]
    if missing:
        raise ValueError("Editor selection missing required fields: " + ", ".join(missing))
    expected = f"{selection['home_team']} vs {selection['away_team']}"
    if selection["selected_match"] != expected:
        raise ValueError("selected_match must equal '<home_team> vs <away_team>'.")


def editor_fixture(selection: dict[str, Any]) -> dict[str, Any]:
    validate_editor_selection(selection)
    return {
        "home_team": selection["home_team"],
        "away_team": selection["away_team"],
        "competition": selection["competition"],
        "kickoff_time": selection["kickoff_time"],
        "country": selection.get("country", "Editor Selected"),
        "audience_interest": 10,
        "importance": 10,
        "rivalry": 8,
        "available_data": 8,
        "story_potential": 10,
        "selection_source": "human_editor",
        "match_priority": selection["match_priority"],
    }


def apply_editor_selection(daily_input: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    fixture = editor_fixture(selection)
    updated = dict(daily_input)
    metadata = dict(updated.get("production_metadata", {}))
    metadata.update(
        {
            "date": selection["production_date"],
            "production_id": selection["production_id"],
            "competition": selection["competition"],
            "match": selection["selected_match"],
            "kickoff_time": selection["kickoff_time"],
            "input_source": "editor_selection",
        }
    )
    updated["production_metadata"] = metadata
    existing = [
        item
        for item in updated.get("fixtures", [])
        if not (
            item.get("home_team") == fixture["home_team"]
            and item.get("away_team") == fixture["away_team"]
            and item.get("competition") == fixture["competition"]
        )
    ]
    updated["fixtures"] = [fixture, *existing]
    updated["editor_selection"] = selection
    context = {
        "recent_form": {
            fixture["home_team"]: "Editor-selected match context: verify latest form before publishing.",
            fixture["away_team"]: "Editor-selected match context: verify latest form before publishing.",
            "summary": "Editor-selected match; automatic sample team context removed.",
        },
        "squad_availability": {
            "confirmed_injuries": [],
            "suspensions": [],
            "fitness_concerns": [],
            "verification_required": True,
        },
        "tactical_notes": {
            "battle": "early pressure vs controlled buildup",
            "playing_style": "Use editor notes and verified match research.",
            "verification_required": True,
        },
        "head_to_head": {"last_five_meetings": [], "historical_trends": "Verify before narration."},
        "statistics": {
            "available_data": "Editor-selected match requires current verification.",
            "first_half_theme": "Opening phase and early pressure should be verified.",
            "verification_required": True,
        },
        "news": {"verification_required": True},
        "betting_market_optional": {},
    }
    context["editor_notes"] = selection["editor_notes"]
    if selection.get("story_angle_optional"):
        context["editor_story_angle"] = selection["story_angle_optional"]
    updated["match_context"] = context
    return updated
