from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASSET_SRC = ROOT / "editorial-brain" / "asset-planner" / "src"
SRC = ROOT / "editorial-brain" / "search-planner" / "src"
sys.path.insert(0, str(ASSET_SRC))
sys.path.insert(0, str(SRC))

from asset_planner.config import load_config as load_asset_config
from asset_planner.json_utils import load_json_file
from asset_planner.service import AssetPlannerService
from search_planner.config import load_config
from search_planner.service import SearchPlannerService


CONFIG_PATH = ROOT / "editorial-brain" / "search-planner" / "config" / "search-planner.config.json"
ASSET_CONFIG_PATH = ROOT / "editorial-brain" / "asset-planner" / "config" / "asset-planner.config.json"
STORYBOARD_PATH = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"


def sample_manifest():
    temp_dir = tempfile.TemporaryDirectory()
    config = replace(load_asset_config(ASSET_CONFIG_PATH), output_directory=Path(temp_dir.name) / "out", log_directory=Path(temp_dir.name) / "logs")
    manifest = AssetPlannerService(config).run(load_json_file(STORYBOARD_PATH))["asset_manifest"]
    temp_dir.cleanup()
    return manifest


class SearchPlannerTests(unittest.TestCase):
    def run_service(self, manifest=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        return SearchPlannerService(config).run(copy.deepcopy(manifest or sample_manifest()))

    def test_missing_assets_create_search_tasks(self):
        result = self.run_service()
        total_tasks = len(result["asset_search_plan"]["search_tasks"]) + len(result["asset_search_plan"]["manual_tasks"]) + len(result["asset_search_plan"]["generation_tasks"])
        self.assertGreater(total_tasks, 0)

    def test_risky_assets_create_legal_review_tasks(self):
        result = self.run_service()
        self.assertTrue(result["asset_search_plan"]["legal_review_tasks"])

    def test_blocked_assets_are_not_approved(self):
        manifest = sample_manifest()
        risky = copy.deepcopy(manifest["required_assets"][0])
        risky["asset_id"] = "broadcast_footage"
        risky["asset_name"] = "Broadcast footage"
        risky["source_strategy"] = "broadcast footage"
        risky["legal_status"] = "blocked"
        manifest["required_assets"].append(risky)
        manifest["missing_assets"].append("broadcast_footage")
        result = self.run_service(manifest)
        self.assertEqual(result["asset_search_plan"]["blocked_assets"][0]["approved_source_type"], "blocked")

    def test_generated_illustration_tasks_are_created_when_needed(self):
        result = self.run_service()
        self.assertTrue(any(task["task_type"] == "generated_illustration" for task in result["asset_search_plan"]["generation_tasks"]))

    def test_fallback_tasks_are_created(self):
        result = self.run_service()
        self.assertTrue(result["asset_search_plan"]["fallback_tasks"])

    def test_search_plan_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()

