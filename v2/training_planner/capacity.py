from __future__ import annotations

from typing import Optional

from config import DEFAULT_EXPERIENCE_FLOOR, PEAK_EQUIVALENTS_5K


def normalize_capacity(percent: int, completed_equivalent_m: int) -> float:
    """Normalize demonstrated equivalent volume against the 5K peak for a rung."""
    peak = PEAK_EQUIVALENTS_5K[percent]
    if peak <= 0:
        return 0.0
    return round(min(max(completed_equivalent_m / peak, 0.0), 1.0), 3)


def target_equivalent_from_capacity(
    percent: int,
    capacity: float,
    recent_best_equivalent: Optional[int],
    experience_floor: float = DEFAULT_EXPERIENCE_FLOOR,
) -> int:
    """Choose a target equivalent volume while respecting recent demonstrated work."""
    peak = PEAK_EQUIVALENTS_5K[percent]
    bounded_capacity = min(max(capacity, 0.0), 1.0)
    capacity_target = peak * bounded_capacity

    if recent_best_equivalent is None:
        target = capacity_target
    else:
        target = max(capacity_target, recent_best_equivalent * max(experience_floor, 0.0))

    target = min(target, peak)
    return max(int(round(target)), 0)
