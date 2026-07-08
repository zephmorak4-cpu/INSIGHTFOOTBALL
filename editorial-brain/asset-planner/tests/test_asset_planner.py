from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "asset-planner" / "src"
sys.path.insert(0, str(SRC))

from asset_planner.config import load_config
from asset_planner.json_utils import load_json_file
from asset_planner.service import AssetPlannerService


CONFIG_PATH = ROOT / "editorial-brain" / "asset-planner" / "config" / "asset-planner.config.json"
STORYBOARD_PATH = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"


class AssetPlannerTests(unittest.TestCase):
    def run_service(self, storyboard=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        return AssetPlannerService(config).run(copy.deepcopy(storyboard if storyboard is not None else load_json_file(STORYBOARD_PATH)))

    def test_valid_final_storyboard_package_creates_asset_manifest(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertTrue(Path(result["asset_manifest_path"]).exists())

    def test_missing_storyboard_package_fails(self):
        result = self.run_service({})
        self.assertFalse(result["success"])

    def test_every_scene_receives_asset_mapping(self):
        result = self.run_service()
        storyboard = load_json_file(STORYBOARD_PATH)
        self.assertEqual(len(result["asset_manifest"]["scene_asset_map"]), len(storyboard["scenes"]))

    def test_required_assets_are_marked_required(self):
        result = self.run_service()
        self.assertTrue(all(asset["required"] for asset in result["asset_manifest"]["required_assets"]))

    def test_optional_assets_are_marked_optional(self):
        result = self.run_service()
        self.assertTrue(all(not asset["required"] for asset in result["asset_manifest"]["optional_assets"]))

    def test_legal_warnings_are_created_for_risky_assets(self):
        result = self.run_service()
        self.assertTrue(any("copyrighted broadcast footage" in warning for warning in result["asset_manifest"]["legal_warnings"]))

    def test_fallback_strategies_exist(self):
        result = self.run_service()
        assets = result["asset_manifest"]["required_assets"] + result["asset_manifest"]["optional_assets"]
        self.assertTrue(all(asset["fallback_strategy"] for asset in assets))

    def test_liverpool_vs_arsenal_sample_succeeds(self):
        result = self.run_service()
        self.assertIn("team_logo_home", result["asset_manifest"]["missing_assets"])


if __name__ == "__main__":
    unittest.main()

