from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchRequest:
    home_team: str
    away_team: str
    competition: str
    raw_text: str
