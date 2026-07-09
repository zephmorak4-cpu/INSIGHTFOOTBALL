from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "editorial-brain" / "creative" / "visual-director" / "src"
sys.path.insert(0, str(SRC))

from visual_director.config import load_config
from visual_director.json_utils import load_json_file
from visual_director.service import VisualDirectorService


CONFIG = ROOT / "editorial-brain" / "creative" / "visual-director" / "config" / "visual-director.config.json"
STORYBOARD = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"
ASSET = ROOT / "editorial-brain" / "output" / "final-asset-package.json"


class VisualDirectorTests(unittest.TestCase):
    def run_service(self, storyboard=None, asset=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(CONFIG), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
        return VisualDirectorService(config).run(copy.deepcopy(storyboard or load_json_file(STORYBOARD)), copy.deepcopy(asset or load_json_file(ASSET)))

    def test_scene_mapping(self):
        result = self.run_service()
        self.assertEqual(len(result["visual_plan"]["scenes"]), len(load_json_file(STORYBOARD)["scenes"]))

    def test_template_mapping(self):
        result = self.run_service()
        self.assertTrue(all(scene["template_id"] for scene in result["visual_plan"]["scenes"]))

    def test_asset_mapping(self):
        result = self.run_service()
        self.assertTrue(all(scene["foreground_assets"] for scene in result["visual_plan"]["scenes"]))

    def test_layout_validation(self):
        result = self.run_service()
        self.assertTrue(result["success"])

    def test_v2_visual_elements_per_scene(self):
        result = self.run_service()
        self.assertTrue(all(len(scene["visual_elements"]) >= 3 for scene in result["visual_plan"]["scenes"]))

    def test_v2_opening_contains_club_and_competition_identity(self):
        opening = self.run_service()["visual_plan"]["scenes"][0]
        required = {"club_badge_home", "club_badge_away", "competition_logo", "match_title", "modern_scoreboard", "broadcast_animation"}
        self.assertTrue(required.issubset(set(opening["visual_elements"])))


if __name__ == "__main__":
    unittest.main()
