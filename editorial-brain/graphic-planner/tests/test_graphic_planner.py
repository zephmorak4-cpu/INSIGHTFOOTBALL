from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ASSET_SRC = ROOT / "editorial-brain" / "asset-planner" / "src"
SEARCH_SRC = ROOT / "editorial-brain" / "search-planner" / "src"
SRC = ROOT / "editorial-brain" / "graphic-planner" / "src"
sys.path.insert(0, str(ASSET_SRC))
sys.path.insert(0, str(SEARCH_SRC))
sys.path.insert(0, str(SRC))

from asset_planner.config import load_config as load_asset_config
from asset_planner.json_utils import load_json_file
from asset_planner.service import AssetPlannerService
from graphic_planner.config import load_config
from graphic_planner.service import GraphicPlannerService
from search_planner.config import load_config as load_search_config
from search_planner.service import SearchPlannerService


CONFIG_PATH = ROOT / "editorial-brain" / "graphic-planner" / "config" / "graphic-planner.config.json"
ASSET_CONFIG_PATH = ROOT / "editorial-brain" / "asset-planner" / "config" / "asset-planner.config.json"
SEARCH_CONFIG_PATH = ROOT / "editorial-brain" / "search-planner" / "config" / "search-planner.config.json"
STORYBOARD_PATH = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"


def sample_inputs():
    temp_dir = tempfile.TemporaryDirectory()
    storyboard = load_json_file(STORYBOARD_PATH)
    asset_config = replace(load_asset_config(ASSET_CONFIG_PATH), output_directory=Path(temp_dir.name) / "asset", log_directory=Path(temp_dir.name) / "logs")
    manifest = AssetPlannerService(asset_config).run(storyboard)["asset_manifest"]
    search_config = replace(load_search_config(SEARCH_CONFIG_PATH), output_directory=Path(temp_dir.name) / "search", log_directory=Path(temp_dir.name) / "logs")
    plan = SearchPlannerService(search_config).run(manifest)["asset_search_plan"]
    temp_dir.cleanup()
    return storyboard, manifest, plan


class GraphicPlannerTests(unittest.TestCase):
    def run_service(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        storyboard, manifest, plan = sample_inputs()
        return GraphicPlannerService(config).run(storyboard, manifest, plan)

    def test_required_graphics_are_created_from_scenes(self):
        result = self.run_service()
        self.assertTrue(result["graphic_requirements"]["required_graphics"])

    def test_dashboard_graphics_are_included(self):
        result = self.run_service()
        self.assertTrue(result["graphic_requirements"]["dashboard_graphics"])

    def test_tactical_graphics_are_included_when_needed(self):
        result = self.run_service()
        self.assertTrue(result["graphic_requirements"]["tactical_graphics"])

    def test_cta_graphics_are_included(self):
        result = self.run_service()
        types = {g["graphic_type"] for g in result["graphic_requirements"]["required_graphics"]}
        self.assertIn("cta_card", types)

    def test_graphic_dimensions_are_valid(self):
        result = self.run_service()
        self.assertTrue(all(g["recommended_dimensions"] == "1080x1920" for g in result["graphic_requirements"]["required_graphics"]))

    def test_scene_graphic_map_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertTrue(result["graphic_requirements"]["scene_graphic_map"])

    def test_final_asset_package_is_created(self):
        result = self.run_service()
        self.assertTrue(Path(result["final_asset_package_path"]).exists())

    def test_missing_assets_are_surfaced(self):
        result = self.run_service()
        self.assertTrue(result["final_asset_package"]["missing_assets"])

    def test_legal_warnings_are_surfaced(self):
        result = self.run_service()
        self.assertTrue(result["final_asset_package"]["legal_warnings"])

    def test_render_readiness_status_is_calculated(self):
        result = self.run_service()
        self.assertIn(result["final_asset_package"]["render_readiness_status"], {"blocked_pending_manual_assets", "ready_for_visual_direction"})

    def test_package_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])

    def test_locked_fields_preserved(self):
        result = self.run_service()
        self.assertEqual(result["final_asset_package"]["locked_fields"], load_json_file(STORYBOARD_PATH)["locked_fields"])


if __name__ == "__main__":
    unittest.main()

