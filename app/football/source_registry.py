from __future__ import annotations


SOURCES = {
    "api_football": {
        "name": "API-Football",
        "provides": ["fixtures", "teams", "recent form", "head-to-head where available", "lineups where available"],
    },
    "gnews": {"name": "GNews", "provides": ["verified recent news headlines"]},
}
