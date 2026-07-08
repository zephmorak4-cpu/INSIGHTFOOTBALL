from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STORYBOARD_SRC = ROOT / "editorial-brain" / "storyboard-generator" / "src"
SCENE_SRC = ROOT / "editorial-brain" / "scene-planner" / "src"
SRC = ROOT / "editorial-brain" / "timing-engine" / "src"
sys.path.insert(0, str(STORYBOARD_SRC))
sys.path.insert(0, str(SCENE_SRC))
sys.path.insert(0, str(SRC))

from scene_planner.config import load_config as load_scene_config
from scene_planner.service import ScenePlannerService
from storyboard_generator.config import load_config as load_storyboard_config
from storyboard_generator.json_utils import load_json_file, load_text_file
from storyboard_generator.service import StoryboardGeneratorService
from timing_engine.config import load_config
from timing_engine.service import TimingEngineService


CONFIG_PATH = ROOT / "editorial-brain" / "timing-engine" / "config" / "timing-engine.config.json"
SCENE_CONFIG_PATH = ROOT / "editorial-brain" / "scene-planner" / "config" / "scene-planner.config.json"
STORYBOARD_CONFIG_PATH = ROOT / "editorial-brain" / "storyboard-generator" / "config" / "storyboard-generator.config.json"
PACKAGE_PATH = ROOT / "editorial-brain" / "output" / "final-script-package.json"
VOICEOVER_PATH = ROOT / "editorial-brain" / "output" / "voiceover_final.txt"


def sample_scene_list():
    temp_dir = tempfile.TemporaryDirectory()
    package = load_json_file(PACKAGE_PATH)
    voiceover = load_text_file(VOICEOVER_PATH)
    storyboard_config = replace(load_storyboard_config(STORYBOARD_CONFIG_PATH), output_directory=Path(temp_dir.name) / "story", log_directory=Path(temp_dir.name) / "logs")
    storyboard = StoryboardGeneratorService(storyboard_config).run(package, voiceover)["storyboard"]
    scene_config = replace(load_scene_config(SCENE_CONFIG_PATH), output_directory=Path(temp_dir.name) / "scene", log_directory=Path(temp_dir.name) / "logs")
    scene_list = ScenePlannerService(scene_config).run(storyboard, package)["scene_list"]
    temp_dir.cleanup()
    return scene_list, voiceover


class TimingEngineTests(unittest.TestCase):
    def run_service(self, scene_list=None, voiceover=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        if scene_list is None:
            scene_list, voiceover = sample_scene_list()
        config = replace(load_config(CONFIG_PATH), output_directory=Path(temp_dir.name) / "output", log_directory=Path(temp_dir.name) / "logs")
        return TimingEngineService(config).run(copy.deepcopy(scene_list), voiceover)

    def test_valid_scene_list_creates_timeline(self):
        result = self.run_service()
        self.assertTrue(result["success"])

    def test_total_duration_over_60_seconds_fails(self):
        scene_list, voiceover = sample_scene_list()
        scene_list["total_duration_seconds"] = 61
        result = self.run_service(scene_list, voiceover)
        self.assertFalse(result["success"])

    def test_overlapping_scenes_fail(self):
        scene_list, voiceover = sample_scene_list()
        scene_list["scenes"][1]["start_time_seconds"] = scene_list["scenes"][0]["start_time_seconds"]
        result = self.run_service(scene_list, voiceover)
        self.assertFalse(result["success"])

    def test_scene_shorter_than_2_seconds_fails(self):
        scene_list, voiceover = sample_scene_list()
        scene_list["scenes"][0]["duration_seconds"] = 1
        result = self.run_service(scene_list, voiceover)
        self.assertFalse(result["success"])

    def test_scene_longer_than_7_seconds_warns_or_fails(self):
        scene_list, voiceover = sample_scene_list()
        scene_list["scenes"][0]["duration_seconds"] = 8
        result = self.run_service(scene_list, voiceover)
        self.assertFalse(result["success"])

    def test_cta_duration_is_valid(self):
        result = self.run_service()
        cta = [scene for scene in result["timeline"]["scenes"] if scene["scene_id"] == "scene-11"][0]
        self.assertGreaterEqual(cta["duration_seconds"], 3)

    def test_dashboard_duration_is_valid(self):
        result = self.run_service()
        dashboard = [scene for scene in result["final_package"]["scenes"] if scene["scene_type"] == "Insight Dashboard"]
        self.assertTrue(dashboard)

    def test_final_storyboard_package_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertEqual(result["final_package"]["next_component"], "Asset Planner")


if __name__ == "__main__":
    unittest.main()

