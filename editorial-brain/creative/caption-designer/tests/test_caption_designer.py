from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VD_SRC = ROOT / "editorial-brain" / "creative" / "visual-director" / "src"
SRC = ROOT / "editorial-brain" / "creative" / "caption-designer" / "src"
sys.path.insert(0, str(VD_SRC))
sys.path.insert(0, str(SRC))

from caption_designer.config import load_config
from caption_designer.service import CaptionDesignerService
from visual_director.config import load_config as load_vd_config
from visual_director.json_utils import load_json_file
from visual_director.service import VisualDirectorService


CONFIG = ROOT / "editorial-brain" / "creative" / "caption-designer" / "config" / "caption-designer.config.json"
VD_CONFIG = ROOT / "editorial-brain" / "creative" / "visual-director" / "config" / "visual-director.config.json"
STORYBOARD = ROOT / "editorial-brain" / "output" / "final-storyboard-package.json"
ASSET = ROOT / "editorial-brain" / "output" / "final-asset-package.json"


def visual_plan():
    temp = tempfile.TemporaryDirectory()
    config = replace(load_vd_config(VD_CONFIG), output_directory=Path(temp.name) / "out", log_directory=Path(temp.name) / "logs")
    plan = VisualDirectorService(config).run(load_json_file(STORYBOARD), load_json_file(ASSET))["visual_plan"]
    temp.cleanup()
    return plan


class CaptionDesignerTests(unittest.TestCase):
    def run_service(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        config = replace(load_config(CONFIG), output_directory=Path(temp.name) / "out")
        return CaptionDesignerService(config).run(visual_plan())

    def test_line_length(self):
        result = self.run_service()
        self.assertTrue(all(len(line.split()) <= 7 for scene in result["caption_plan"]["scenes"] for line in scene["caption"].split("\n")))

    def test_readability(self):
        result = self.run_service()
        self.assertTrue(all(scene["font_size"] >= 46 for scene in result["caption_plan"]["scenes"]))

    def test_safe_area(self):
        result = self.run_service()
        self.assertTrue(all("safe" in scene["caption_position"] for scene in result["caption_plan"]["scenes"]))


if __name__ == "__main__":
    unittest.main()

