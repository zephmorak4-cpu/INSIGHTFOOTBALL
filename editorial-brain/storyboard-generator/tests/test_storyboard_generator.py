from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "editorial-brain" / "storyboard-generator" / "src"
sys.path.insert(0, str(SRC))

from storyboard_generator.config import load_config
from storyboard_generator.json_utils import load_json_file, load_text_file
from storyboard_generator.service import StoryboardGeneratorService


CONFIG_PATH = ROOT / "editorial-brain" / "storyboard-generator" / "config" / "storyboard-generator.config.json"
PACKAGE_PATH = ROOT / "editorial-brain" / "output" / "final-script-package.json"
VOICEOVER_PATH = ROOT / "editorial-brain" / "output" / "voiceover_final.txt"


def test_config(temp: Path):
    return replace(load_config(CONFIG_PATH), output_directory=temp / "output", log_directory=temp / "logs")


class StoryboardGeneratorTests(unittest.TestCase):
    def run_service(self, package=None, voiceover=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        package = copy.deepcopy(package or load_json_file(PACKAGE_PATH))
        voiceover = load_text_file(VOICEOVER_PATH) if voiceover is None else voiceover
        return StoryboardGeneratorService(test_config(Path(temp_dir.name))).run(package, voiceover)

    def test_valid_final_script_package_creates_storyboard_draft(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertTrue(Path(result["storyboard_path"]).exists())

    def test_missing_voiceover_fails(self):
        result = self.run_service(voiceover="")
        self.assertFalse(result["success"])

    def test_missing_production_id_fails(self):
        package = load_json_file(PACKAGE_PATH)
        package["production_id"] = ""
        result = self.run_service(package=package)
        self.assertFalse(result["success"])

    def test_scene_count_is_reasonable(self):
        result = self.run_service()
        self.assertGreaterEqual(result["storyboard"]["scene_count"], 8)
        self.assertLessEqual(result["storyboard"]["scene_count"], 12)

    def test_all_scenes_contain_voiceover_text(self):
        result = self.run_service()
        self.assertTrue(all(scene["voiceover_text"] for scene in result["storyboard"]["scenes"]))

    def test_required_scene_fields_exist(self):
        result = self.run_service()
        required = {"scene_id", "scene_number", "scene_type", "start_time_seconds", "end_time_seconds", "duration_seconds", "voiceover_text", "caption_text", "on_screen_text", "required_assets"}
        self.assertTrue(all(required.issubset(scene) for scene in result["storyboard"]["scenes"]))

    def test_locked_fields_preserved(self):
        result = self.run_service()
        self.assertEqual(result["storyboard"]["locked_fields"], load_json_file(PACKAGE_PATH)["locked_fields"])

    def test_liverpool_vs_arsenal_sample_succeeds(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertLessEqual(result["storyboard"]["total_estimated_duration_seconds"], 60)


if __name__ == "__main__":
    unittest.main()

