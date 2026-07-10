from __future__ import annotations

from app.utils.text import slugify


def build_directors_sheet(fixture: dict[str, str], script: str) -> str:
    sentences = [part.strip() for part in script.replace("?", "?.").split(".") if part.strip()]
    duration = 60
    step = max(3, duration // max(len(sentences), 12))
    lines = [f"# Director's Sheet - {fixture['home_team']} vs {fixture['away_team']}", "", "Open this file while editing in CapCut.", ""]
    start = 0
    for index, sentence in enumerate(sentences[:18], start=1):
        end = min(60, start + step)
        visual = "tactical pitch graphic" if index % 3 == 0 else "statistic card" if index % 2 == 0 else "team badge"
        lines.extend([
            f"## Moment {index}: {start:02d}s-{end:02d}s",
            f"- narration: {sentence}",
            "- purpose: Move the story forward with one clear visual.",
            f"- recommended_visual_type: {visual}",
            f"- exact_visual_description: Create a clean INSIGHT FOOTBALL branded 9:16 graphic showing {fixture['home_team']} and {fixture['away_team']} with the relevant phrase highlighted.",
            f"- primary_search_keywords: {fixture['home_team']} badge, {fixture['away_team']} badge, {fixture['competition']} logo",
            "- alternative_search_keywords: football pitch graphic, football crowd, tactical arrows",
            "- recommended_source: Canva or CapCut-built graphic; rights check required for real club/player images.",
            f"- on_screen_text: {sentence[:70]}",
            "- graphic_instruction: dark navy background, red accent line, white readable text.",
            "- capcut_instruction: add subtle push-in motion and keep captions clear.",
            "- transition: clean swipe",
            "- motion: slow zoom or left-to-right reveal",
            "- asset_priority: team badges, competition logo, pitch graphic",
            "- fallback_visual: text-only emphasis screen with team colors.",
            "",
        ])
        start = end
        if start >= 60:
            break
    return "\n".join(lines)


def directors_filename(home: str, away: str) -> str:
    return f"{slugify(home)}-vs-{slugify(away)}-directors-sheet.md"
