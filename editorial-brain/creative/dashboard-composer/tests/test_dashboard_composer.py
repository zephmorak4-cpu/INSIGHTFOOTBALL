from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VD_SRC = ROOT / "editorial-brain" / "creative" / "visual-director" / "src"
CAM_SRC = ROOT / "editorial-brain" / "creative" / "camera-planner" / "src"
MOT_SRC = ROOT / "editorial-brain" / "creative" / "motion-planner" / "src"
CAP_SRC = ROOT / "editorial-brain" / "creative" / "caption-designer" / "src"
SRC = ROOT / "editorial-brain" / "creative" / "dashboard-composer" / "src"
for path in [VD_SRC, CAM_SRC, MOT_SRC, CAP_SRC, SRC]:
    sys.path.insert(0, str(path))

from camera_planner.config import load_config as load_camera_config
from camera_planner.service import CameraPlannerService
from caption_designer.config import load_config as load_caption_config
from caption_designer.service import CaptionDesignerService
from dashboard_composer.config import load_config
from dashboard_composer.service import DashboardComposerService
from motion_planner.config import load_config as load_motion_config
from motion_planner.service import MotionPlannerService
from visual_director.config import load_config as load_vd_config
from visual_director.json_utils import load_json_file
from visual_director.service import VisualDirectorService


BASE = ROOT / "editorial-brain" / "creative"
STORYBOARD = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"
ASSET = ROOT / "editorial-brain" / "output" / "final-asset-package.json"


def sample_inputs():
    temp = tempfile.TemporaryDirectory()
    out = Path(temp.name)
    storyboard = load_json_file(STORYBOARD)
    vd = replace(load_vd_config(BASE / "visual-director" / "config" / "visual-director.config.json"), output_directory=out / "vd", log_directory=out / "logs")
    visual = VisualDirectorService(vd).run(storyboard, load_json_file(ASSET))["visual_plan"]
    camera = CameraPlannerService(replace(load_camera_config(BASE / "camera-planner" / "config" / "camera-planner.config.json"), output_directory=out / "cam")).run(visual)["camera_plan"]
    motion = MotionPlannerService(replace(load_motion_config(BASE / "motion-planner" / "config" / "motion-planner.config.json"), output_directory=out / "mot")).run(visual)["motion_plan"]
    captions = CaptionDesignerService(replace(load_caption_config(BASE / "caption-designer" / "config" / "caption-designer.config.json"), output_directory=out / "cap")).run(visual)["caption_plan"]
    temp.cleanup()
    return storyboard, visual, camera, motion, captions


class DashboardComposerTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(BASE / "dashboard-composer" / "config" / "dashboard-composer.config.json"), output_directory=Path(temp.name) / "out")
        return DashboardComposerService(config).run(*sample_inputs())

    def test_dashboard_completeness(self):
        result = self.run_service()
        self.assertEqual(len(result["dashboard_plan"]["dashboard_cards"]), 5)

    def test_icon_mapping(self):
        result = self.run_service()
        self.assertTrue(all(card["icon"] for card in result["dashboard_plan"]["dashboard_cards"]))

    def test_animation_timing(self):
        result = self.run_service()
        self.assertTrue(all(card["display_time"] > 0 for card in result["dashboard_plan"]["dashboard_cards"]))

    def test_visual_production_package_validates(self):
        result = self.run_service()
        self.assertTrue(result["success"])
        self.assertTrue(result["visual_production_package"]["validation_report"]["all_scenes_covered"])


if __name__ == "__main__":
    unittest.main()

