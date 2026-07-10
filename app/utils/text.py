from __future__ import annotations

import re


PROHIBITED_SCRIPT_PHRASES = ["safe bet", "banker", "sure win"]
INTERNAL_LABELS = ["Wildcard", "Tactical Edge", "Form Index", "Risk Meter", "X-Factor", "Probability Engine", "Intelligence Report"]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
