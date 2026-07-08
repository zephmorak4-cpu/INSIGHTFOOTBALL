from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VD_SRC = ROOT / "editorial-brain" / "creative" / "visual-director" / "src"
SRC = ROOT / "editorial-brain" / "creative" / "camera-planner" / "src"
sys.path.insert(0, str(VD_SRC))
sys.path.insert(0, str(SRC))

from camera_planner.config import load_config
from camera_planner.service import CameraPlannerService
from visual_director.config import load_config as load_vd_config
from visual_director.json_utils import load_json_file
from visual_director.service import VisualDirectorService


CONFIG = ROOT / "editorial-brain" / "creative" / "camera-planner" / "config" / "camera-planner.config.json"
VD_CONFIG = ROOT / "editorial-brain" / "creative" / "visual-director" / "config" / "visual-director.config.json"
STORYBOARD = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"
ASSET = ROOT / "editorial-brain" / "output" / "final-asset-package.json"


def visual_plan():
    temp = tempfile.TemporaryDirectory()
    config = replace(load_vd_config(VD_CONFIG), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
    plan = VisualDirectorService(config).run(load_json_file(STORYBOARD), load_json_file(ASSET))["visual_plan"]
    temp.cleanup()
    return plan


class CameraPlannerTests(unittest.TestCase):
    def run_service(self, plan=None, config_override=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(CONFIG), output_directory=Path(temp.name) / "out")
        if config_override:
            config = config_override(config)
        return CameraPlannerService(config).run(copy.deepcopy(plan or visual_plan()))

    def test_valid_movement(self):
        result = self.run_service()
        allowed = set(load_config(CONFIG).allowed_camera_moves)
        self.assertTrue(all(scene["camera_preset"] in allowed for scene in result["camera_plan"]["scenes"]))

    def test_no_unsupported_camera(self):
        result = self.run_service(config_override=lambda c: replace(c, allowed_camera_moves=["Static"]))
        self.assertFalse(result["success"])

    def test_duration_validation(self):
        result = self.run_service()
        self.assertTrue(all(scene["camera_duration"] > 0 for scene in result["camera_plan"]["scenes"]))


if __name__ == "__main__":
    unittest.main()

