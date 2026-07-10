from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Fixture:
    fixture_id: str
    home_team: str
    away_team: str
    competition: str
    kickoff_time: str
    venue: str | None
    status: str
    source: str


@dataclass
class DataItem:
    value: Any
    source: str
    fetched_at: str
    verified: bool
    confidence: float


@dataclass
class MatchData:
    fixture: Fixture
    categories: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
