from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "readiness_check.py"
spec = importlib.util.spec_from_file_location("readiness_check", SCRIPT)
readiness = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["readiness_check"] = readiness
spec.loader.exec_module(readiness)


class ReadinessCheckTests(unittest.TestCase):
    def test_render_config_ready(self):
        self.assertTrue(readiness.render_config_ready())

    def test_env_set_does_not_expose_value(self):
        self.assertFalse(readiness.env_set("INSIGHT_FOOTBALL_TEST_SECRET_THAT_SHOULD_NOT_EXIST"))


if __name__ == "__main__":
    unittest.main()
