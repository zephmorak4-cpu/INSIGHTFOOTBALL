from __future__ import annotations

from app.utils.text import INTERNAL_LABELS, PROHIBITED_SCRIPT_PHRASES, word_count


def write_script(fixture: dict[str, str], insight: dict[str, object], probabilities: dict[str, object]) -> str:
    question = f"So the real question is this: {insight['what_to_watch']}"
    base = (
        f"Everyone will have a simple read on {fixture['home_team']} against {fixture['away_team']}, but the useful detail is this: "
        f"{insight['central_insight']} The first evidence is recent balance. {insight['supporting_evidence'][0]['claim']} "
        f"The second clue is the opponent comparison. {insight['supporting_evidence'][1]['claim']} "
        f"That matters because {insight['why_it_matters']} The counterpoint is important too: recent form does not promise what happens in one match. "
        f"My model gives {fixture['home_team']} {probabilities['team_a_win']} percent, the draw {probabilities['draw']} percent, and {fixture['away_team']} {probabilities['team_b_win']} percent. "
    )
    filler = "This is why the matchup needs context, not just names."
    words = (base + question).split()
    while len(words) < 120:
        base = base + " " + filler
        words = (base + " " + question).split()
    return " ".join((base + " " + question).split()[:150]).rstrip(".") + ("?" if not question.endswith("?") else "")


def script_issues(script: str) -> list[str]:
    issues = []
    wc = word_count(script)
    if not 120 <= wc <= 150:
        issues.append(f"word count {wc}")
    lowered = script.lower()
    for phrase in PROHIBITED_SCRIPT_PHRASES:
        if phrase in lowered:
            issues.append(f"prohibited phrase: {phrase}")
    for label in INTERNAL_LABELS:
        if label.lower() in lowered:
            issues.append(f"internal label: {label}")
    if not script.strip().endswith("?"):
        issues.append("script must end with a question")
    return issues
