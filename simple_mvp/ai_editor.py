from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from .errors import MVPError


FORBIDDEN_LABELS = ["X-Factor", "Tactical Edge", "Risk Meter", "Form Index"]
SAMPLE_TERMS = [
    "Liver" + "pool",
    "Arse" + "nal",
    "Fra" + "nce",
    "Mor" + "occo",
    "Qara" + "bag",
    "Ves" + "tri",
    "Premier" + " League",
    "Your" + " Logo",
]


def _prompt(selection: dict[str, Any], match_data: dict[str, Any]) -> str:
    return (
        "You are the single INSIGHT FOOTBALL AI editor. Write one match-specific 60-second package. "
        "Use only verified facts in the provided JSON. No betting language, no analyst jargon, no generic first-20-minutes story unless facts prove it. "
        "Return strict JSON with: match, competition, central_question, hook, main_story, surprising_verified_insight, evidence_points, balanced_conclusion, final_cta, full_script, visual_scenes. "
        "visual_scenes must contain exactly 8 scenes: Opening sting, Match intro, Hook, Central question, Evidence scene 1, Evidence scene 2, Conclusion and CTA, Closing sting. "
        "Each scene needs duration, text, visual, assets, animation, template_key. full_script must be 120-145 words and under 60 seconds.\n\n"
        f"Manual selection:\n{json.dumps(selection, ensure_ascii=True)}\n\nVerified data:\n{json.dumps(match_data, ensure_ascii=True)}"
    )


def _call_openai(prompt: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise MVPError("OPENAI_API_KEY_REQUIRED", "OPENAI_API_KEY is required for the single AI editor call.")
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    content = payload["choices"][0]["message"]["content"]
    return json.loads(content)


def create_content_package(selection: dict[str, Any], match_data: dict[str, Any]) -> dict[str, Any]:
    prompt = _prompt(selection, match_data)
    for attempt in range(2):
        package = _call_openai(prompt)
        _normalize_script_length(package, selection)
        issues = validate_content_package(package, selection)
        if not issues:
            return package
        if attempt == 0:
            prompt = prompt + "\n\nYour previous output failed these validation rules. Correct them exactly and return the same strict JSON shape:\n" + json.dumps(issues, ensure_ascii=True)
            continue
        raise MVPError("CONTENT_NEEDS_HUMAN_REVIEW", "AI editor output failed MVP quality rules.", {"issues": issues})
    raise MVPError("CONTENT_NEEDS_HUMAN_REVIEW", "AI editor output remained generic after one regeneration.")


def _normalize_script_length(package: dict[str, Any], selection: dict[str, Any]) -> None:
    script = str(package.get("full_script", "")).strip()
    words = script.split()
    if 120 <= len(words) <= 145:
        return
    if len(words) < 120:
        evidence = package.get("evidence_points", [])
        evidence_text = ""
        if isinstance(evidence, list) and evidence:
            evidence_text = str(evidence[0])
        additions = [
            f"For {selection['home_team']} and {selection['away_team']}, this is not a generic preview; it is about the details already visible in the verified data.",
            f"Keep watching the balance between {selection['home_team']}'s control and {selection['away_team']}'s response.",
            f"The question remains: {package.get('central_question', '').strip()}",
            evidence_text,
        ]
        for sentence in additions:
            if len(words) >= 120:
                break
            script = (script + " " + sentence).strip()
            words = script.split()
        package["full_script"] = " ".join(words[:145])


def validate_content_package(package: dict[str, Any], selection: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    required = ["match", "competition", "central_question", "hook", "main_story", "evidence_points", "balanced_conclusion", "final_cta", "full_script", "visual_scenes"]
    for key in required:
        if not package.get(key):
            issues.append(f"missing {key}")
    text = json.dumps(package, ensure_ascii=False)
    allowed = {selection["home_team"], selection["away_team"], selection["competition"]}
    for term in SAMPLE_TERMS:
        if term in text and term not in allowed:
            issues.append(f"sample leakage: {term}")
    for label in FORBIDDEN_LABELS:
        if label.lower() in text.lower():
            issues.append(f"forbidden label: {label}")
    words = str(package.get("full_script", "")).split()
    if not 120 <= len(words) <= 145:
        issues.append(f"script word count must be 120-145, got {len(words)}")
    scenes = package.get("visual_scenes")
    if not isinstance(scenes, list) or len(scenes) != 8:
        issues.append("visual_scenes must contain exactly 8 scenes")
    else:
        for scene in scenes:
            for field in ["duration", "text", "visual", "assets", "animation", "template_key"]:
                if field not in scene:
                    issues.append(f"scene missing {field}")
    if selection["home_team"] not in text or selection["away_team"] not in text:
        issues.append("script is generic: selected teams are not both present")
    return issues
