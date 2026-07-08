"""Voiceover metrics."""

from __future__ import annotations


def count_words(text: str) -> int:
    return len([word for word in str(text).replace("...", " ").split() if word.strip()])


def estimate_duration_seconds(text: str) -> int:
    return max(1, round(count_words(text) / 2.6))

