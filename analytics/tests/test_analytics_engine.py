from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "analytics" / "shared"
sys.path.insert(0, str(SRC))

from analytics_engine.core import (
    cta_analyzer,
    daily_performance_reporter,
    hook_analyzer,
    metrics_collector,
    performance_analyzer,
    performance_database,
    recommendation_engine,
    retention_analyzer,
    run_all,
    thumbnail_analyzer,
)
from analytics_engine.io import load_json
from analytics_engine.providers import FacebookInsightsAdapter, TelegramStatisticsAdapter, YouTubeAnalyticsAdapter

PACKAGE = ROOT / "editorial-brain" / "output" / "published-package.json"


class AnalyticsEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_json(PACKAGE)

    def build(self):
        metrics = metrics_collector(self.package, root=ROOT)
        db = performance_database(self.package, metrics, root=ROOT)
        performance = performance_analyzer(metrics, db, root=ROOT)
        hooks = hook_analyzer(db, root=ROOT)
        thumbnails = thumbnail_analyzer(db, root=ROOT)
        retention = retention_analyzer(metrics, root=ROOT)
        cta = cta_analyzer(db, root=ROOT)
        recs = recommendation_engine(performance, hooks, thumbnails, retention, cta, root=ROOT)
        return metrics, db, performance, hooks, thumbnails, retention, cta, recs

    def test_provider_abstraction(self):
        self.assertEqual(YouTubeAnalyticsAdapter().provider_name, "youtube")
        self.assertEqual(FacebookInsightsAdapter().provider_name, "facebook")
        self.assertEqual(TelegramStatisticsAdapter().provider_name, "telegram")

    def test_metrics_parses_metrics(self):
        metrics = metrics_collector(self.package, root=ROOT)
        self.assertGreater(metrics["totals"]["views"], 0)

    def test_metrics_validates_metrics(self):
        metrics = metrics_collector(self.package, root=ROOT)
        for platform in metrics["platforms"]:
            self.assertIn("average_view_duration_seconds", platform)

    def test_database_stores_history(self):
        metrics = metrics_collector(self.package, root=ROOT)
        db = performance_database(self.package, metrics, root=ROOT)
        self.assertTrue(any(video["production_id"] == self.package["production_id"] for video in db["videos"]))

    def test_database_retrieves_history(self):
        _, db, *_ = self.build()
        self.assertGreaterEqual(len(db["videos"]), 3)

    def test_performance_compares_averages(self):
        _, _, performance, *_ = self.build()
        self.assertIn("views_vs_average_percent", performance)

    def test_hook_analyzer_ranks_hooks(self):
        _, _, _, hooks, *_ = self.build()
        self.assertGreater(len(hooks["hook_leaderboard"]), 0)

    def test_thumbnail_analyzer_ranks_thumbnails(self):
        _, _, _, _, thumbnails, *_ = self.build()
        self.assertGreater(len(thumbnails["thumbnail_leaderboard"]), 0)

    def test_retention_detects_dropoff(self):
        _, _, _, _, _, retention, *_ = self.build()
        self.assertLess(retention["primary_drop_off"]["retention_percent"], 40)

    def test_cta_analyzer_ranks_ctas(self):
        *_, cta, _ = self.build()
        self.assertGreater(len(cta["cta_leaderboard"]), 0)

    def test_recommendation_engine_generates_recommendations(self):
        *_, recs = self.build()
        self.assertGreater(len(recs["recommendations"]), 0)

    def test_recommendation_engine_never_modifies_prompts(self):
        *_, recs = self.build()
        self.assertFalse(recs["prompt_rewrite_performed"])

    def test_reporter_generates_reports(self):
        metrics, db, performance, hooks, thumbnails, retention, cta, recs = self.build()
        reports = daily_performance_reporter(db, performance, hooks, thumbnails, retention, cta, recs, root=ROOT)
        self.assertIn("daily_report", reports)
        self.assertIn("weekly_report", reports)
        self.assertIn("monthly_report", reports)

    def test_learning_package_created(self):
        result = run_all(ROOT)
        self.assertEqual(result["learning_package"]["approval_status"], "approved")

    def test_learning_package_summary(self):
        package = run_all(ROOT)["learning_package"]
        self.assertIn("platform_metrics", package)
        self.assertIn("recommendations", package)


if __name__ == "__main__":
    unittest.main()
