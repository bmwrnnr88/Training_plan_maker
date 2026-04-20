from __future__ import annotations

from typing import Dict, Iterable, Tuple

from config import PHASE_QUOTAS_5K
from history import count_percent_exposures, get_recent_sessions, days_since_percent
from models import Phase, SessionRecord

PHASE_EMPHASIS = {
    "general": {
        80: 6.0,
        85: 5.0,
        90: 5.0,
        95: 4.0,
        100: -2.0,
        105: -5.0,
        110: -6.0,
        115: 1.0,
    },
    "supportive": {
        80: -8.0,
        85: -4.0,
        90: 5.0,
        95: 8.0,
        100: 8.0,
        105: 6.0,
        110: 0.0,
        115: -3.0,
    },
    "specific": {
        80: -8.0,
        85: -6.0,
        90: 2.0,
        95: 8.0,
        100: 8.0,
        105: 8.0,
        110: 2.0,
        115: 2.0,
    },
}


def _quota_score(phase: Phase, percent: int, history: Iterable[SessionRecord]) -> Tuple[float, str]:
    quota = PHASE_QUOTAS_5K[phase][percent]
    exposures = count_percent_exposures(history, percent, quota["window_days"])

    if exposures < quota["target_min"]:
        deficit = quota["target_min"] - exposures
        return deficit * 12.0, f"under target in the {quota['window_days']}-day window"

    if exposures > quota["target_max"]:
        overflow = exposures - quota["target_max"]
        return -(overflow * 9.0), "already well covered recently"

    return 2.0, "within recent phase quota"


def _recency_score(percent: int, history: Iterable[SessionRecord]) -> Tuple[float, str]:
    days_since = days_since_percent(history, percent)

    if days_since is None:
        return 6.0, "not touched recently"
    if days_since <= 2:
        return -7.0, "very recent exposure"
    if days_since <= 5:
        return -3.0, "recently used"
    if days_since <= 9:
        return 1.0, "ready for another touch"
    return 4.0, "has been out of the mix for a while"


def _capacity_score(percent: int, capacities: Dict[int, float]) -> Tuple[float, str]:
    capacity = min(max(capacities.get(percent, 0.0), 0.0), 1.0)
    weakness_score = (1.0 - capacity) * 5.0
    if capacity < 0.45:
        return weakness_score, "capacity is currently underbuilt here"
    if capacity < 0.7:
        return weakness_score, "capacity could use reinforcement"
    return weakness_score / 2.0, "capacity is already reasonably established"


def _phase_emphasis_score(phase: Phase, percent: int) -> Tuple[float, str]:
    emphasis = PHASE_EMPHASIS[phase][percent]

    if emphasis >= 4.5:
        return emphasis, "this rung is a core phase emphasis"
    if emphasis >= 1.0:
        return emphasis, "this rung fits the phase well"
    if emphasis <= -3.0:
        return emphasis, "this rung is de-emphasized in this phase"
    if emphasis < 0.0:
        return emphasis, "this rung is only a secondary touch right now"
    return emphasis, "this rung is mainly maintenance in this phase"


def _readiness_penalty(percent: int, readiness: int) -> Tuple[float, str]:
    if readiness <= 2 and percent >= 105:
        return -12.0, "readiness is too low for a high-demand rung"
    if readiness <= 2 and percent >= 100:
        return -7.0, "readiness favors lower-cost work today"
    if readiness == 3 and percent >= 110:
        return -6.0, "readiness discourages the highest-stress options"
    if readiness == 3 and percent >= 105:
        return -2.0, "readiness slightly softens the faster options"
    if readiness >= 4 and percent >= 100:
        return 1.5, "readiness can support quality work"
    return 0.0, "readiness is neutral here"


def _recent_load_penalty(percent: int, history: Iterable[SessionRecord]) -> Tuple[float, str]:
    recent_sessions = get_recent_sessions(history, 4)
    if not recent_sessions:
        return 0.0, "no short-term load penalty"

    recent_load = sum(session.load_score for session in recent_sessions)
    latest_load = recent_sessions[0].load_score

    if percent >= 105 and (recent_load >= 55.0 or latest_load >= 35.0):
        return -10.0, "recent load is too dense for another hard high rung"
    if percent >= 100 and (recent_load >= 70.0 or latest_load >= 45.0):
        return -6.0, "recent load suggests a little more spacing"
    if percent <= 95 and recent_load >= 70.0:
        return -2.0, "recent load nudges toward steadier support work"
    return 0.0, "recent load spacing is acceptable"


def select_candidate_percent(
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> tuple[int, str]:
    """Select the primary percent rung that best fits current needs."""
    candidates = sorted(PHASE_QUOTAS_5K[phase].keys())
    scored_candidates = []

    for percent in candidates:
        quota_points, quota_reason = _quota_score(phase, percent, history)
        recency_points, recency_reason = _recency_score(percent, history)
        capacity_points, capacity_reason = _capacity_score(percent, capacities)
        phase_points, phase_reason = _phase_emphasis_score(phase, percent)
        readiness_points, readiness_reason = _readiness_penalty(percent, readiness)
        load_points, load_reason = _recent_load_penalty(percent, history)

        total_score = (
            quota_points
            + recency_points
            + capacity_points
            + phase_points
            + readiness_points
            + load_points
        )

        scored_candidates.append(
            (
                total_score,
                percent,
                [
                    quota_reason,
                    phase_reason,
                    recency_reason,
                    capacity_reason,
                    readiness_reason,
                    load_reason,
                ],
            )
        )

    scored_candidates.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    _, selected_percent, reasons = scored_candidates[0]
    reason_summary = "; ".join(reason for reason in reasons[:3])
    return selected_percent, reason_summary
