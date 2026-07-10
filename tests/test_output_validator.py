from __future__ import annotations

import unittest

from app.content.output_validator import validate_outputs


class OutputValidatorTests(unittest.TestCase):
    def test_output_validation_passes(self):
        script = " ".join(["Chelsea"] * 120) + "?"
        insight = {"central_insight": "specific", "supporting_evidence": [{}, {}]}
        probs = {"team_a_win": 34, "draw": 30, "team_b_win": 36}
        result = validate_outputs("Sources Used", insight, probs, script, "Moment\nCapCut")
        self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
