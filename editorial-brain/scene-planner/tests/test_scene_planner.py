from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STORYBOARD_SRC = ROOT / "editorial-brain" / "storyboard-generator" / "src"
SRC = ROOT / "editorial-brain" / "scene-planner" / "src"
sys.path.insert(0, str(STORYBOARD_SRC))
sys.path.insert(0, str(SRC))

from scene_planner.config import load_config
from scene_planner.service import ScenePlannerService
from storyboard_generator.config import load_config as load_storyboard_config
from storyboard_generator.json_utils import load_json_file, load_text_file
from storyboard_generator.service import StoryboardGeneratorService


CONFIG_PATH = ROOT / "editorial-brain" / "scene-planner" / "config" / "scene-planner.config.json"
STORYBOARD_CONFIG_PATH = ROOT / "editorial-brain" / "storyboard-generator" / "config" / "storyboard-generator.config.json"
PACKAGE_PATH = ROOT / "editorial-brain" / "output" / "final-script-package.json"
VOICEOVER_PATH = ROOT / "editorial-brain" / "output" / "voiceover_final.txt"


def sample_inputs():
    temp_dir = tempfile.TemporaryDirectory()
    config = replace(load_storyboard_config(STORYBOARD_CONFIG_PATH), output_directory=Path(temp_dir.name) / "out", log_directory=Path(temp_dir.name) / "logs")
    package = load_json_file(PACKAGE_PATH)
    voiceover = load_text_file(VOICEOVER_PATH)
    storyboard = StoryboardGeneratorService(config).run(package, voiceover)["storyboard"]
    temp_dir.cleanup()
    return storyboard, package


class ScenePlannerTests(unittest.TestCase):
    def run_service(self, storyboard=None, package=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        storyboard, package = (storyboard, package) if storyboard is not None else sample_inputs()
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        return ScenePlannerService(config).run(copy.deepcopy(storyboard), copy.deepcopy(package))

    def test_valid_storyboard_draft_creates_scene_list(self):
        result = self.run_service()
        self.assertTrue(result["success"])

    def test_unknown_scene_type_fails(self):
        storyboard, package = sample_inputs()
        storyboard["scenes"][0]["scene_type"] = "Unknown"
        result = self.run_service(storyboard, package)
        self.assertFalse(result["success"])

    def test_missing_caption_fails(self):
        storyboard, package = sample_inputs()
        storyboard["scenes"][0]["caption_text"] = ""
        result = self.run_service(storyboard, package)
        self.assertFalse(result["success"])

    def test_overloaded_scene_is_flagged(self):
        storyboard, package = sample_inputs()
        storyboard["scenes"][0]["voiceover_text"] = "word " * 30
        result = self.run_service(storyboard, package)
        self.assertFalse(result["success"])

    def test_cta_scene_exists(self):
        result = self.run_service()
        self.assertIn("Final Question / CTA", {scene["scene_type"] for scene in result["scene_list"]["scenes"]})

    def test_dashboard_scene_exists(self):
        result = self.run_service()
        self.assertIn("Insight Dashboard", {scene["scene_type"] for scene in result["scene_list"]["scenes"]})

    def test_scene_list_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertEqual(result["scene_list"]["approval_status"], "approved")


if __name__ == "__main__":
    unittest.main()

