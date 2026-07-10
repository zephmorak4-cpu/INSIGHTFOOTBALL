from __future__ import annotations


def cap_confidence(value: float, data_quality: str) -> float:
    if data_quality == "INSUFFICIENT":
        return min(value, 0.35)
    if data_quality == "PARTIAL":
        return min(value, 0.65)
    return min(value, 0.9)
