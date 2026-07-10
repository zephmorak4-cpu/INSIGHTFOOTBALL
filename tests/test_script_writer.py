from __future__ import annotations

import unittest

from app.content.script_writer import script_issues, write_script


class ScriptWriterTests(unittest.TestCase):
    def test_script_word_count_and_no_prohibited_phrases(self):
        fixture = {"home_team": "Chelsea", "away_team": "Arsenal"}
        insight = {"central_insight": "Chelsea's defensive balance matters.", "supporting_evidence": [{"claim": "Chelsea conceded 3."}, {"claim": "Arsenal scored 6."}], "why_it_matters": "it decides territory.", "what_to_watch": "Can Arsenal force Chelsea wide?"}
        probabilities = {"team_a_win": 35, "draw": 30, "team_b_win": 35}
        script = write_script(fixture, insight, probabilities)
        self.assertFalse(script_issues(script))


if __name__ == "__main__":
    unittest.main()
