from __future__ import annotations

import unittest

from app.intelligence.insight_discovery import discover_insight


class InsightDiscoveryTests(unittest.TestCase):
    def test_insight_schema(self):
        normalized = {"fixture": {"home_team": "Chelsea", "away_team": "Arsenal"}, "categories": {"recent_form": {"Chelsea": {"last_5": {"value": {"goals_scored": 8, "goals_conceded": 3}}}, "Arsenal": {"last_5": {"value": {"goals_scored": 6, "goals_conceded": 4}}}}}}
        result = discover_insight(normalized, "")
        self.assertIn("central_insight", result)
        self.assertEqual(len(result["supporting_evidence"]), 2)


if __name__ == "__main__":
    unittest.main()
