from __future__ import annotations

import os
import urllib.parse
from typing import Any


def resolve_assets(selection: dict[str, Any]) -> dict[str, Any]:
    logo = os.environ.get("INSIGHT_FOOTBALL_LOGO_URL", "").strip()
    home = selection["home_team"]
    away = selection["away_team"]
    return {
        "brand_logo": logo,
        "home_badge": _asset_url("HOME_BADGE_URL", home),
        "away_badge": _asset_url("AWAY_BADGE_URL", away),
        "competition_logo": _asset_url("COMPETITION_LOGO_URL", selection["competition"]),
        "stadium_background": os.environ.get("STADIUM_BACKGROUND_URL", _placeholder_url("Dark stadium background")),
        "pitch_graphic": os.environ.get("PITCH_GRAPHIC_URL", _placeholder_url("Pitch graphic")),
        "tactical_arrows": os.environ.get("TACTICAL_ARROWS_URL", _placeholder_url("Tactical arrows")),
        "icons": {"simple": os.environ.get("SIMPLE_ICON_URL", _placeholder_url("Football icon"))},
        "warnings": [] if logo else ["INSIGHT_FOOTBALL_LOGO_URL missing; renderer must reject live production until configured."],
    }


def _asset_url(env_name: str, label: str) -> str:
    return os.environ.get(env_name, _placeholder_url(label))


def _placeholder_url(label: str) -> str:
    encoded = urllib.parse.quote(label)
    return f"https://placehold.co/600x600/0B132B/F5F5F5.png?text={encoded}"
