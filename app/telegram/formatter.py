from __future__ import annotations

from app.models.football_models import Fixture
from app.utils.text import word_count


def format_match_found(fixture: Fixture, run_id: str) -> str:
    return "\n".join(["INSIGHT FOOTBALL - MATCH FOUND", "", f"Match: {fixture.home_team} vs {fixture.away_team}", f"Competition: {fixture.competition}", f"Kickoff: {fixture.kickoff_time}", f"Venue: {fixture.venue or 'Unavailable'}", f"Run ID: {run_id}"])


def format_script(script: str, probabilities: dict[str, object], confidence: float) -> str:
    return "\n".join(["60-SECOND SCRIPT", "", script, "", f"Word count: {word_count(script)}", "Estimated speaking time: 55-65 seconds", f"Probabilities: {probabilities['team_a_win']}% / {probabilities['draw']}% / {probabilities['team_b_win']}%", f"Data confidence: {confidence:.2f}"])


def format_health(status: dict[str, object]) -> str:
    return "\n".join([f"{key}: {value}" for key, value in status.items()])
