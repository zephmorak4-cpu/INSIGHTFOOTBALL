"""Timing metrics."""

from __future__ import annotations


def count_words(text: str) -> int:
    return len([word for word in str(text).replace("...", " ").split() if word.strip()])


def speech_duration(text: str) -> float:
    return round(count_words(text) / 2.6, 2)

