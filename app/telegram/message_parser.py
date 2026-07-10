from __future__ import annotations

import re

from app.models.output_models import AppError
from app.models.request_models import MatchRequest


FORMAT_HINT = "Please send the match in this format:\n\nChelsea vs Arsenal\nPremier League"


def parse_match_message(text: str, run_id: str = "") -> MatchRequest:
    cleaned = text.strip()
    if not cleaned or cleaned.startswith("/"):
        raise AppError("INVALID_INPUT", "message_parser", FORMAT_HINT, False, run_id)
    if "|" in cleaned:
        left, competition = [part.strip() for part in cleaned.split("|", 1)]
        teams = left
    else:
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if len(lines) == 1 and lines[0].lower().startswith("match:"):
            raise AppError("INVALID_INPUT", "message_parser", FORMAT_HINT, False, run_id)
        if len(lines) == 1 and "competition:" in lines[0].lower():
            teams = re.sub(r"^match:\s*", "", lines[0].split("Competition:", 1)[0], flags=re.I).strip()
            competition = lines[0].split("Competition:", 1)[1].strip()
        elif len(lines) >= 2:
            teams = re.sub(r"^match:\s*", "", lines[0], flags=re.I).strip()
            competition = re.sub(r"^competition:\s*", "", lines[1], flags=re.I).strip()
        else:
            raise AppError("INVALID_INPUT", "message_parser", FORMAT_HINT, False, run_id)
    match = re.match(r"^(.+?)\s+(?:vs|v|versus)\s+(.+)$", teams, flags=re.I)
    if not match or not competition:
        raise AppError("INVALID_INPUT", "message_parser", FORMAT_HINT, False, run_id)
    return MatchRequest(home_team=match.group(1).strip(), away_team=match.group(2).strip(), competition=competition.strip(), raw_text=text)
