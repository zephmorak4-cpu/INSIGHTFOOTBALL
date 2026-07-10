from __future__ import annotations

import unittest

from app.football.data_validator import validate_data
from app.models.request_models import MatchRequest


class DataValidatorTests(unittest.TestCase):
    def test_data_sufficiency(self):
        normalized = {"fixture": {"home_team": "Chelsea", "away_team": "Arsenal", "competition": "Premier League", "kickoff_time": "2099-01-01T12:00:00+00:00"}, "categories": {"match_context": {}, "recent_form": {"Chelsea": {}, "Arsenal": {}}, "head_to_head": {}, "news": []}}
        result = validate_data(MatchRequest("Chelsea", "Arsenal", "Premier League", ""), normalized)
        self.assertIn(result["status"], {"SUFFICIENT", "PARTIAL"})


if __name__ == "__main__":
    unittest.main()
