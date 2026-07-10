from __future__ import annotations

import unittest
from unittest.mock import patch

from app.config.settings import Settings
from app.football.fixture_resolver import resolve_fixture
from app.models.output_models import AppError
from app.models.request_models import MatchRequest


class FixtureResolverTests(unittest.TestCase):
    def test_fixture_resolution(self):
        payload = {"response": [{"fixture": {"id": 1, "date": "2099-01-01T12:00:00+00:00", "venue": {"name": "Bridge"}, "status": {"short": "NS"}}, "teams": {"home": {"name": "Chelsea"}, "away": {"name": "Arsenal"}}, "league": {"name": "Premier League"}}]}
        with patch("app.football.fixture_resolver._api_get", return_value=payload):
            fixture = resolve_fixture(MatchRequest("Chelsea", "Arsenal", "Premier League", ""), Settings(football_api_key="key"), "r1")
        self.assertEqual(fixture.fixture_id, "1")

    def test_missing_fixture(self):
        with patch("app.football.fixture_resolver._api_get", return_value={"response": []}):
            with self.assertRaises(AppError) as ctx:
                resolve_fixture(MatchRequest("Chelsea", "Arsenal", "Premier League", ""), Settings(football_api_key="key"), "r1")
        self.assertEqual(ctx.exception.code, "FIXTURE_NOT_FOUND")

    def test_ambiguous_fixture(self):
        item = {"fixture": {"date": "2099-01-01T12:00:00+00:00", "venue": {}, "status": {}}, "teams": {"home": {"name": "Chelsea"}, "away": {"name": "Arsenal"}}, "league": {"name": "Premier League"}}
        payload = {"response": [{**item, "fixture": {**item["fixture"], "id": 1}}, {**item, "fixture": {**item["fixture"], "id": 2}}]}
        with patch("app.football.fixture_resolver._api_get", return_value=payload):
            with self.assertRaises(AppError) as ctx:
                resolve_fixture(MatchRequest("Chelsea", "Arsenal", "Premier League", ""), Settings(football_api_key="key"), "r1")
        self.assertEqual(ctx.exception.code, "AMBIGUOUS_FIXTURE")


if __name__ == "__main__":
    unittest.main()
