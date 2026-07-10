from __future__ import annotations

import unittest

from app.intelligence.report_builder import build_report


class ReportBuilderTests(unittest.TestCase):
    def test_report_has_required_sections(self):
        normalized = {"fixture": {"home_team": "Chelsea", "away_team": "Arsenal", "competition": "Premier League", "kickoff_time": "2099", "venue": "Bridge"}, "categories": {"recent_form": {}}, "sources": ["API-Football"]}
        report = build_report(normalized, {"status": "PARTIAL", "missing_categories": []})
        self.assertIn("Match Overview", report)
        self.assertIn("Sources Used", report)


if __name__ == "__main__":
    unittest.main()
