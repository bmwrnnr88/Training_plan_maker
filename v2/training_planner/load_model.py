from __future__ import annotations

from typing import Dict

from config import LOAD_THRESHOLDS, LOAD_WEIGHTS


def compute_load(minutes_by_percent: Dict[int, float], rest_minutes: float) -> float:
    """Compute a session load score from percent-specific work and rest."""
    load_score = 0.0

    for percent, minutes in minutes_by_percent.items():
        weight = LOAD_WEIGHTS.get(percent, LOAD_WEIGHTS["easy"])
        load_score += max(minutes, 0.0) * weight

    load_score += max(rest_minutes, 0.0) * LOAD_WEIGHTS["rest"]
    return round(load_score, 2)


def classify_load(load_score: float) -> str:
    """Map a load score to its load class."""
    if load_score < LOAD_THRESHOLDS["easy_max"]:
        return "easy"
    if load_score <= LOAD_THRESHOLDS["moderate_max"]:
        return "moderate"
    if load_score <= LOAD_THRESHOLDS["hard_max"]:
        return "hard"
    return "very_hard"
