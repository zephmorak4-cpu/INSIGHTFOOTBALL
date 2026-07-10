from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.models.football_models import MatchData


def normalize_match_data(data: MatchData) -> dict[str, Any]:
    payload = {"fixture": asdict(data.fixture), "categories": data.categories, "sources": data.sources}
    return _normalize_percentages(payload)


def _normalize_percentages(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
