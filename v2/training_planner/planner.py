from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from capacity import target_equivalent_from_capacity
from history import days_since_percent, get_recent_sessions, recent_best_equivalent
from load_model import classify_load
from models import PercentWorkout, Phase, PlannerResult, SessionRecord
from selector import select_candidate_percent
from utils import sort_workouts
from workouts_5k import WORKOUT_DB_5K


def _recent_load_state(history: Iterable[SessionRecord]) -> Tuple[float, float]:
    recent_sessions = get_recent_sessions(history, 5)
    if not recent_sessions:
        return 0.0, 0.0

    total_load = sum(session.load_score for session in recent_sessions)
    latest_load = recent_sessions[0].load_score
    return total_load, latest_load


def _recent_primary_sessions(
    history: Iterable[SessionRecord],
    percent: int,
    days: int = 42,
) -> List[SessionRecord]:
    """Return recent sessions where the chosen percent was the main session focus."""
    return [
        session
        for session in get_recent_sessions(history, days)
        if session.primary_percent == percent
    ]


def _match_previous_template(
    session: SessionRecord,
    candidates: List[PercentWorkout],
) -> Optional[PercentWorkout]:
    """Infer which template a prior completed session most closely matches."""
    exact_text_match = next(
        (candidate for candidate in candidates if candidate.workout_text == session.workout_text),
        None,
    )
    if exact_text_match is not None:
        return exact_text_match

    session_secondary = tuple(session.secondary_percents)
    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (
            abs(candidate.equivalent_volume_m - session.equivalent_volume_m),
            candidate.secondary_percents != list(session_secondary),
            abs(candidate.load_estimate - session.load_score),
            candidate.progression_order,
        ),
    )
    return ranked_candidates[0] if ranked_candidates else None


def _desired_progression_order(
    previous_workout: Optional[PercentWorkout],
    target_equivalent: int,
    readiness: int,
    recent_total_load: float,
    latest_load: float,
    days_since_same_percent: Optional[int],
    max_progression_order: int,
) -> Tuple[Optional[int], str]:
    """Estimate whether the athlete should hold, step forward, or downshift."""
    if previous_workout is None:
        return None, "no recent same-percent progression anchor"

    if readiness <= 2 or recent_total_load >= 70.0 or latest_load >= 40.0:
        return max(previous_workout.progression_order - 1, 1), "recent readiness/load points to a lighter step"

    if days_since_same_percent is not None and days_since_same_percent <= 6:
        return previous_workout.progression_order, "same percent was used recently, so hold the ladder"

    equivalent_ratio = target_equivalent / max(previous_workout.equivalent_volume_m, 1)
    if readiness >= 4 and equivalent_ratio >= 1.03:
        next_order = min(previous_workout.progression_order + 1, max_progression_order)
        return next_order, "capacity/readiness support a one-step progression"

    if equivalent_ratio < 0.92:
        return max(previous_workout.progression_order - 1, 1), "current target points to a more segmented version"

    return previous_workout.progression_order, "recent history supports staying near the demonstrated level"


def _progression_score(
    workout: PercentWorkout,
    previous_workout: Optional[PercentWorkout],
    desired_order: Optional[int],
) -> float:
    """Reward workouts that stay close to the athlete's recent progression path."""
    if previous_workout is None or desired_order is None:
        return 0.0

    order_gap = abs(workout.progression_order - desired_order)
    score = 18.0 - (order_gap * 7.0)

    if workout.family == previous_workout.family:
        score += 8.0
    elif workout.build_direction == previous_workout.build_direction:
        score += 4.0

    if workout.progression_order > previous_workout.progression_order + 1:
        score -= 6.0
    if workout.progression_order < previous_workout.progression_order - 1:
        score -= 5.0

    return score


def _complexity_score(
    workout: PercentWorkout,
    capacity: float,
    readiness: int,
    phase: Phase,
) -> float:
    """Bias toward simpler builds when the athlete is not ready for added complexity."""
    complexity = 0
    if workout.secondary_percents:
        complexity += 1
    if workout.build_direction in {"blend", "combo", "top_down"}:
        complexity += 1

    score = 0.0
    if capacity < 0.7 or readiness <= 3:
        score -= complexity * 5.0
        if workout.build_direction in {"single_percent", "bottom_up", "alternation", "maintenance"}:
            score += 2.0

    if phase == "specific" and capacity >= 0.7 and readiness >= 4 and complexity > 0:
        score += 3.0

    return score


def _score_workout(
    workout: PercentWorkout,
    target_equivalent: int,
    recent_best: int | None,
    readiness: int,
    recent_total_load: float,
    latest_load: float,
    previous_workout: Optional[PercentWorkout],
    desired_progression_order: Optional[int],
    capacity: float,
    phase: Phase,
) -> float:
    target_gap = abs(workout.equivalent_volume_m - target_equivalent)
    score = 100.0 - (target_gap / 150.0)

    if recent_best is not None:
        if workout.equivalent_volume_m >= recent_best * 0.9:
            score += 10.0
        else:
            score -= 10.0

    if readiness <= 2:
        score -= workout.progression_order * 4.0
        score -= max(workout.difficulty_rank - 2, 0) * 3.0
    elif readiness == 3:
        score -= max(workout.progression_order - 3, 0) * 2.5
    else:
        score += min(workout.progression_order, 4) * 1.5

    if recent_total_load >= 70.0:
        score -= workout.load_estimate * 0.5
    elif recent_total_load <= 25.0 and readiness >= 4:
        score += min(workout.load_estimate, 35.0) * 0.15

    if latest_load >= 40.0:
        score -= workout.difficulty_rank * 2.0

    if workout.anti_regression_floor and recent_best is not None:
        score += 4.0

    score += _progression_score(
        workout=workout,
        previous_workout=previous_workout,
        desired_order=desired_progression_order,
    )
    score += _complexity_score(
        workout=workout,
        capacity=capacity,
        readiness=readiness,
        phase=phase,
    )

    return score


def select_workout_template(
    percent: int,
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> PlannerResult:
    """Select the best-fitting workout template for a chosen percent rung."""
    candidates: List[PercentWorkout] = [
        workout
        for workout in WORKOUT_DB_5K
        if workout.primary_percent == percent
        and phase in workout.phase_fit
        and capacities.get(percent, 0.0) >= workout.minimum_capacity
        and readiness >= workout.minimum_readiness
    ]

    if not candidates:
        raise ValueError(f"No workout templates are available for {percent}% in {phase}.")

    recent_best = recent_best_equivalent(history, percent)
    recent_same_percent_sessions = _recent_primary_sessions(history, percent)
    previous_workout = (
        _match_previous_template(recent_same_percent_sessions[0], candidates)
        if recent_same_percent_sessions
        else None
    )
    target_equivalent = target_equivalent_from_capacity(
        percent=percent,
        capacity=capacities.get(percent, 0.0),
        recent_best_equivalent=recent_best,
    )
    recent_total_load, latest_load = _recent_load_state(history)
    desired_progression_order, progression_reason = _desired_progression_order(
        previous_workout=previous_workout,
        target_equivalent=target_equivalent,
        readiness=readiness,
        recent_total_load=recent_total_load,
        latest_load=latest_load,
        days_since_same_percent=days_since_percent(history, percent),
        max_progression_order=max(workout.progression_order for workout in candidates),
    )

    scored_candidates = []
    for workout in sort_workouts(candidates):
        score = _score_workout(
            workout=workout,
            target_equivalent=target_equivalent,
            recent_best=recent_best,
            readiness=readiness,
            recent_total_load=recent_total_load,
            latest_load=latest_load,
            previous_workout=previous_workout,
            desired_progression_order=desired_progression_order,
            capacity=capacities.get(percent, 0.0),
            phase=phase,
        )
        scored_candidates.append((score, workout))

    scored_candidates.sort(
        key=lambda item: (
            item[0],
            -abs(item[1].equivalent_volume_m - target_equivalent),
            -item[1].progression_order,
        ),
        reverse=True,
    )
    selected_workout = scored_candidates[0][1]

    reason_bits = [
        f"capacity target points to about {target_equivalent}m equivalent at {percent}%",
        f"recent best is {recent_best}m" if recent_best is not None else "no anti-regression floor is active yet",
        progression_reason,
        f"recent load is {recent_total_load:.1f} over the last five days",
    ]

    return PlannerResult(
        selected_percent=percent,
        selected_workout_id=selected_workout.id,
        workout_text=selected_workout.workout_text,
        secondary_percents=selected_workout.secondary_percents,
        load_estimate=selected_workout.load_estimate,
        load_class=classify_load(selected_workout.load_estimate),
        reason_summary="; ".join(reason_bits),
    )


def generate_next_workout(
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> PlannerResult:
    """Generate the next workout from percent selection through template selection."""
    selected_percent, percent_reason = select_candidate_percent(
        phase=phase,
        capacities=capacities,
        history=history,
        readiness=readiness,
    )
    workout_result = select_workout_template(
        percent=selected_percent,
        phase=phase,
        capacities=capacities,
        history=history,
        readiness=readiness,
    )
    workout_result.reason_summary = f"{percent_reason}; {workout_result.reason_summary}"
    return workout_result
