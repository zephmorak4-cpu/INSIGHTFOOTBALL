from __future__ import annotations

import unittest

from app.models.output_models import AppError
from app.telegram.message_parser import parse_match_message


class MessageParserTests(unittest.TestCase):
    def test_valid_multiline_input(self):
        result = parse_match_message("Chelsea vs Arsenal\nPremier League")
        self.assertEqual(result.home_team, "Chelsea")
        self.assertEqual(result.away_team, "Arsenal")
        self.assertEqual(result.competition, "Premier League")

    def test_valid_pipe_input(self):
        result = parse_match_message("Chelsea vs Arsenal | Premier League")
        self.assertEqual(result.competition, "Premier League")

    def test_invalid_input(self):
        with self.assertRaises(AppError):
            parse_match_message("hello football")


if __name__ == "__main__":
    unittest.main()
