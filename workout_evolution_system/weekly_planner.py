from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional

from workout_evolution_system.progression import (
    describe_workout,
    next_progression_for_band,
    progress_ratio_for_band,
    workout_volume_miles,
)
from workout_evolution_system.utils import round_to_half_mile


SYSTEM_BANDS = {
    "endurance": [85, 90, 95],
    "race": [100],
    "cv": [105],
    "speed": [110, 115],
}

PHASE_BANDS = {
    "general": [90, 105, 110, 85],
    "race-supportive": [90, 95, 105, 110],
    "race-specific": [95, 100, 105, 90],
}

ADJACENT_BANDS = {
    85: [90],
    90: [95, 85],
    95: [90, 100],
    100: [95, 105],
    105: [100, 110],
    110: [105, 115],
    115: [110],
}


def generate_weekly_plan(
    states: Dict[int, Dict[str, object]],
    ladder: Dict[int, Dict[str, float | str]],
    phase: str,
    limiter: Optional[str] = None,
) -> Dict[str, object]:
    progressions = {band: progress_ratio_for_band(state) for band, state in states.items()}
    primary_band = _select_primary_band(progressions, phase=phase, limiter=limiter)
    support_band = _select_support_band(progressions, primary_band=primary_band)

    primary_next = next_progression_for_band(states[primary_band], ladder)
    support_next = next_progression_for_band(states[support_band], ladder)

    future_states = deepcopy(states)
    future_states[primary_band] = primary_next["state"]
    future_states[support_band] = support_next["state"]

    peak_metrics = _peak_aerobic_work(future_states)
    long_run_low = round_to_half_mile(peak_metrics["peak_aerobic_work"] * 1.5)
    long_run_high = round_to_half_mile(peak_metrics["peak_aerobic_work"] * 2.0)
    long_run_recommended = round_to_half_mile((long_run_low + long_run_high) / 2.0)

    quality_total = workout_volume_miles(primary_next["state"]) + workout_volume_miles(support_next["state"])
    weekly_target = round_to_half_mile((quality_total + long_run_recommended) * 2.0)

    sunday_is_off = phase == "race-specific"
    easy_days = 3 if sunday_is_off else 4
    easy_miles = round_to_half_mile(
        max(4.0, (weekly_target - quality_total - long_run_recommended) / easy_days)
    )
    easy_pace = ladder[80]["pace_per_mile"]

    schedule = [
        {"day": "Monday", "session": f"{easy_miles:.1f} mi easy @ {easy_pace}/mi"},
        {"day": "Tuesday", "session": describe_workout(primary_next["state"], ladder)},
        {"day": "Wednesday", "session": f"{easy_miles:.1f} mi easy @ {easy_pace}/mi"},
        {"day": "Thursday", "session": describe_workout(support_next["state"], ladder)},
        {"day": "Friday", "session": f"{easy_miles:.1f} mi easy @ {easy_pace}/mi"},
        {
            "day": "Saturday",
            "session": (
                f"{long_run_recommended:.1f} mi long run @ {easy_pace}/mi "
                f"(range {long_run_low:.1f}-{long_run_high:.1f})"
            ),
        },
        {
            "day": "Sunday",
            "session": "Off" if sunday_is_off else f"{easy_miles:.1f} mi easy @ {easy_pace}/mi",
        },
    ]

    notes = [
        f"Primary workout is {primary_band}% because it is the weakest eligible band in the {phase} phase.",
        f"Supporting workout is {support_band}%, chosen as the adjacent support band.",
        f"Peak aerobic work is {peak_metrics['peak_aerobic_work']:.1f} mi from {peak_metrics['driver']}.",
        "Paces stay fixed from the initial 5k baseline; only workout shape changes.",
    ]

    if limiter:
        notes.insert(0, f"User limiter applied: {limiter}.")

    return {
        "phase": phase,
        "primary_band": primary_band,
        "support_band": support_band,
        "primary_workout": primary_next,
        "support_workout": support_next,
        "peak_metrics": peak_metrics,
        "long_run": {
            "recommended": long_run_recommended,
            "minimum": long_run_low,
            "maximum": long_run_high,
        },
        "weekly_target_miles": weekly_target,
        "schedule": schedule,
        "notes": notes,
    }


def _select_primary_band(
    progressions: Dict[int, float],
    phase: str,
    limiter: Optional[str],
) -> int:
    phase_candidates = PHASE_BANDS[phase]

    if limiter:
        limiter_key = limiter.lower()
        if limiter_key in SYSTEM_BANDS:
            candidates = [band for band in SYSTEM_BANDS[limiter_key] if band in phase_candidates]
            if not candidates:
                candidates = SYSTEM_BANDS[limiter_key]
            return min(candidates, key=lambda band: (progressions[band], phase_candidates.index(band) if band in phase_candidates else 99))

    return min(phase_candidates, key=lambda band: progressions[band])


def _select_support_band(progressions: Dict[int, float], primary_band: int) -> int:
    candidates = ADJACENT_BANDS[primary_band]
    return min(candidates, key=lambda band: (progressions[band], band))


def _peak_aerobic_work(states: Dict[int, Dict[str, object]]) -> Dict[str, float | str]:
    threshold_work = workout_volume_miles(states[95])
    race_work = workout_volume_miles(states[100])
    steady_work = max(
        workout_volume_miles(states[85]),
        workout_volume_miles(states[90]),
    )

    components = {
        "threshold_work": threshold_work,
        "race_work": race_work,
        "steady_run": steady_work,
    }

    driver, peak_value = max(
        (
            ("threshold work", threshold_work),
            ("race-pace work", race_work),
            ("longest steady run", steady_work),
        ),
        key=lambda item: item[1],
    )

    return {
        **components,
        "peak_aerobic_work": peak_value,
        "driver": driver,
    }
