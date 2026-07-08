from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VD_SRC = ROOT / "editorial-brain" / "creative" / "visual-director" / "src"
SRC = ROOT / "editorial-brain" / "creative" / "motion-planner" / "src"
sys.path.insert(0, str(VD_SRC))
sys.path.insert(0, str(SRC))

from motion_planner.config import load_config
from motion_planner.service import MotionPlannerService
from visual_director.config import load_config as load_vd_config
from visual_director.json_utils import load_json_file
from visual_director.service import VisualDirectorService


CONFIG = ROOT / "editorial-brain" / "creative" / "motion-planner" / "config" / "motion-planner.config.json"
VD_CONFIG = ROOT / "editorial-brain" / "creative" / "visual-director" / "config" / "visual-director.config.json"
STORYBOARD = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"
ASSET = ROOT / "editorial-brain" / "output" / "final-asset-package.json"


def visual_plan():
    temp = tempfile.TemporaryDirectory()
    config = replace(load_vd_config(VD_CONFIG), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
    plan = VisualDirectorService(config).run(load_json_file(STORYBOARD), load_json_file(ASSET))["visual_plan"]
    temp.cleanup()
    return plan


class MotionPlannerTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(CONFIG), output_directory=Path(temp.name) / "out")
        return MotionPlannerService(config).run(visual_plan())

    def test_valid_preset(self):
        result = self.run_service()
        allowed = set(load_config(CONFIG).allowed_motion_presets)
        self.assertTrue(all(scene["motion_preset"] in allowed for scene in result["motion_plan"]["scenes"]))

    def test_timing_validation(self):
        result = self.run_service()
        self.assertTrue(all(scene["duration"] > 0 for scene in result["motion_plan"]["scenes"]))

    def test_animation_purpose(self):
        result = self.run_service()
        self.assertTrue(all(scene["animation_reason"] for scene in result["motion_plan"]["scenes"]))


if __name__ == "__main__":
    unittest.main()

