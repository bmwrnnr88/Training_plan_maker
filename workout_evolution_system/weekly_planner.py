from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional

from workout_evolution_system.event_profiles import band_weight, candidate_bands, phase_from_weeks
from workout_evolution_system.progression import (
    describe_workout,
    next_progression_for_band,
    peak_state_for_band,
    progress_ratio_to_peak,
    recommend_rest_seconds,
    workout_volume_miles,
)
from workout_evolution_system.utils import clamp, meters_to_miles, round_to_half_mile


SYSTEM_BANDS = {
    "endurance": [85, 90, 95],
    "race": [100],
    "cv": [105],
    "speed": [110, 115],
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

BAND_STRESS_FACTORS = {
    80: 0.6,
    85: 0.8,
    90: 1.0,
    95: 1.25,
    100: 1.4,
    105: 1.2,
    110: 1.0,
    115: 0.85,
}

TYPE_STRESS_FACTORS = {
    "continuous": 1.2,
    "broken_tempo": 1.1,
    "interval": 1.0,
}

DAY_STYLE_MULTIPLIERS = {
    "off": 0.0,
    "shakeout": 0.55,
    "very_easy": 0.7,
    "easy": 1.0,
    "easy_strides": 1.0,
    "easy_to_steady": 1.15,
    "steady": 1.25,
}


def generate_weekly_plan(
    states: Dict[int, Dict[str, object]],
    ladder: Dict[int, Dict[str, float | str]],
    goal_event: str,
    weeks_to_goal: int,
    allow_peak_extension: bool,
    limiter: Optional[str] = None,
) -> Dict[str, object]:
    phase = phase_from_weeks(goal_event, weeks_to_goal)
    peak_states = {band: peak_state_for_band(goal_event, band, ladder) for band in states}
    progressions = {
        band: progress_ratio_to_peak(state, peak_states[band]) for band, state in states.items()
    }
    stimulus_scores = {
        band: _stimulus_priority(
            progress_ratio=progressions[band],
            recent_sessions=int(states[band].get("recent_sessions_21d", 0)),
            days_since_last=int(states[band].get("days_since_last", 7)),
        )
        for band in states
    }
    primary_band = _select_primary_band(
        goal_event=goal_event,
        progressions=progressions,
        stimulus_scores=stimulus_scores,
        phase=phase,
        limiter=limiter,
    )
    support_band = _select_support_band(
        progressions=progressions,
        stimulus_scores=stimulus_scores,
        primary_band=primary_band,
    )

    primary_next = next_progression_for_band(
        states[primary_band],
        ladder,
        goal_event=goal_event,
        allow_extension=allow_peak_extension,
    )
    support_next = next_progression_for_band(
        states[support_band],
        ladder,
        goal_event=goal_event,
        allow_extension=allow_peak_extension,
    )

    future_states = deepcopy(states)
    future_states[primary_band] = primary_next["state"]
    future_states[support_band] = support_next["state"]

    peak_metrics = _peak_aerobic_work(future_states)
    long_run_low = round_to_half_mile(peak_metrics["peak_aerobic_work"] * 1.5)
    long_run_high = round_to_half_mile(peak_metrics["peak_aerobic_work"] * 2.0)
    long_run_recommended = round_to_half_mile((long_run_low + long_run_high) / 2.0)

    primary_stress = _session_stress(primary_next["state"], ladder)
    support_stress = _session_stress(support_next["state"], ladder)
    workout_stress_total = primary_stress + support_stress
    workout_stress_tier = _stress_tier(workout_stress_total)

    long_run = _build_long_run_session(
        phase=phase,
        long_run_miles=long_run_recommended,
        primary_band=primary_band,
        support_band=support_band,
        stress_tier=workout_stress_tier,
        ladder=ladder,
    )
    weekly_stress_total = workout_stress_total + long_run["stress"]
    weekly_stress_tier = _stress_tier(weekly_stress_total)

    base_easy_miles = round_to_half_mile(
        clamp(long_run_recommended * 0.42, 4.0, 8.5)
    )
    recovery_templates = _recovery_templates(
        phase=phase,
        primary_stress_tier=_stress_tier(primary_stress),
        support_stress_tier=_stress_tier(support_stress),
        weekly_stress_tier=weekly_stress_tier,
        long_run_style=long_run["style"],
    )

    monday = _build_aerobic_day(recovery_templates["Monday"], base_easy_miles, ladder)
    wednesday = _build_aerobic_day(recovery_templates["Wednesday"], base_easy_miles, ladder)
    friday = _build_aerobic_day(recovery_templates["Friday"], base_easy_miles, ladder)
    sunday = _build_aerobic_day(recovery_templates["Sunday"], base_easy_miles, ladder)

    quality_total = workout_volume_miles(primary_next["state"]) + workout_volume_miles(support_next["state"])
    weekly_target = round_to_half_mile(
        quality_total
        + long_run["miles"]
        + monday["miles"]
        + wednesday["miles"]
        + friday["miles"]
        + sunday["miles"]
    )

    phase_candidates = set(candidate_bands(goal_event, phase))
    selection_table = []
    for band in sorted(states):
        role = ""
        if band == primary_band:
            role = "primary"
        elif band == support_band:
            role = "support"

        phase_weight = band_weight(goal_event, phase, band)
        selection_table.append(
            {
                "band": f"{band}%",
                "role": role or "available",
                "candidate_this_phase": band in phase_candidates,
                "progress_to_peak": round(progressions[band] * 100),
                "recent_sessions_21d": int(states[band].get("recent_sessions_21d", 0)),
                "days_since_last": int(states[band].get("days_since_last", 7)),
                "stimulus_need": stimulus_scores[band],
                "phase_weight": round(phase_weight, 2),
                "selection_priority": round(stimulus_scores[band] * phase_weight, 3),
            }
        )

    schedule = [
        {"day": "Monday", "session": monday["session"]},
        {"day": "Tuesday", "session": describe_workout(primary_next["state"], ladder)},
        {"day": "Wednesday", "session": wednesday["session"]},
        {"day": "Thursday", "session": describe_workout(support_next["state"], ladder)},
        {"day": "Friday", "session": friday["session"]},
        {"day": "Saturday", "session": long_run["session"]},
        {"day": "Sunday", "session": sunday["session"]},
    ]

    notes = [
        (
            f"Primary workout is {primary_band}% because its combination of goal-race relevance, "
            f"progress deficit, and recent-training freshness is highest in the {phase} phase."
        ),
        f"Supporting workout is {support_band}%, chosen as the most useful adjacent support band.",
        f"Goal race is {goal_event}; phase is auto-derived from {weeks_to_goal} weeks to race.",
        f"Peak aerobic work is {peak_metrics['peak_aerobic_work']:.1f} mi from {peak_metrics['driver']}.",
        (
            "Easy-day structure follows the ladder-of-support phase figure: general training keeps more 80-85% "
            "aerobic support, while race-specific weeks trade those days for easier recovery."
        ),
        (
            "Recent training matters through two inputs: how many sessions you have done at each band in the "
            "last 21 days, and how many days ago that band last appeared."
        ),
        (
            f"Weekly stress tier is {weekly_stress_tier}; non-workout days are adjusted around that stress "
            f"instead of splitting leftover mileage evenly."
        ),
        "Paces stay fixed from the initial 5k baseline; only workout shape changes.",
    ]

    if limiter:
        notes.insert(0, f"User limiter applied: {limiter}.")

    return {
        "phase": phase,
        "primary_band": primary_band,
        "support_band": support_band,
        "progressions": progressions,
        "stimulus_scores": stimulus_scores,
        "primary_workout": primary_next,
        "support_workout": support_next,
        "peak_metrics": peak_metrics,
        "selection_table": selection_table,
        "long_run": {
            "recommended": long_run["miles"],
            "minimum": long_run_low,
            "maximum": long_run_high,
            "style": long_run["style"],
        },
        "weekly_target_miles": weekly_target,
        "schedule": schedule,
        "notes": notes,
    }


def _select_primary_band(
    goal_event: str,
    progressions: Dict[int, float],
    stimulus_scores: Dict[int, float],
    phase: str,
    limiter: Optional[str],
) -> int:
    phase_candidates = candidate_bands(goal_event, phase)

    if limiter:
        limiter_key = limiter.lower()
        if limiter_key in SYSTEM_BANDS:
            candidates = [band for band in SYSTEM_BANDS[limiter_key] if band in phase_candidates]
            if not candidates:
                candidates = SYSTEM_BANDS[limiter_key]
            return max(
                candidates,
                key=lambda band: (
                    stimulus_scores[band] * band_weight(goal_event, phase, band),
                    -progressions[band],
                    -phase_candidates.index(band) if band in phase_candidates else -99,
                ),
            )

    return max(
        phase_candidates,
        key=lambda band: (
            stimulus_scores[band] * band_weight(goal_event, phase, band),
            -progressions[band],
        ),
    )


def _select_support_band(
    progressions: Dict[int, float],
    stimulus_scores: Dict[int, float],
    primary_band: int,
) -> int:
    candidates = ADJACENT_BANDS[primary_band]
    return max(candidates, key=lambda band: (stimulus_scores[band], -progressions[band], -band))


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


def _stimulus_priority(progress_ratio: float, recent_sessions: int, days_since_last: int) -> float:
    deficit = 1.0 - clamp(progress_ratio, 0.0, 1.0)
    freshness = clamp(days_since_last / 10.0, 0.55, 1.2)
    recency_penalty = 1.0 if recent_sessions <= 1 else 0.85 if recent_sessions == 2 else 0.68
    return round(deficit * freshness * recency_penalty, 3)


def _session_stress(state: Dict[int, Dict[str, object]] | Dict[str, object], ladder: Dict[int, Dict[str, float | str]]) -> float:
    band = int(state["band"])
    current = state["current"]
    workout_type = current["type"]
    volume = workout_volume_miles(state)

    stress = volume * BAND_STRESS_FACTORS[band] * TYPE_STRESS_FACTORS[workout_type]

    if workout_type == "interval":
        rep_distance_m = int(current.get("distance_m", 0))
        rep_miles = meters_to_miles(rep_distance_m)
        work_duration = ladder[band]["seconds_per_mile"] * rep_miles
        actual_rest = int(current.get("rest_sec", 0))
        recommended_rest = recommend_rest_seconds(band=band, work_duration_seconds=work_duration)
        density_factor = clamp(recommended_rest / max(actual_rest, 30), 0.85, 1.2)
        extension_factor = 0.9 + (rep_miles * 0.25)
        stress *= density_factor * extension_factor
    elif workout_type == "continuous":
        continuous_miles = float(current.get("distance_miles", 0.0))
        stress *= 1.0 + (max(0.0, continuous_miles - 4.0) * 0.03)
    elif workout_type == "broken_tempo":
        segment_miles = float(current.get("distance_miles", 0.0))
        stress *= 0.95 + (segment_miles * 0.04)

    return round(stress, 1)


def _stress_tier(stress: float) -> str:
    if stress >= 22:
        return "very_high"
    if stress >= 15:
        return "high"
    if stress >= 9:
        return "moderate"
    return "low"


def _build_long_run_session(
    phase: str,
    long_run_miles: float,
    primary_band: int,
    support_band: int,
    stress_tier: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    easy_pace = ladder[80]["pace_per_mile"]
    steady_pace = ladder[85]["pace_per_mile"]
    supportive_pace = ladder[90]["pace_per_mile"]

    if phase == "general":
        if stress_tier == "low":
            finish_miles = round_to_half_mile(clamp(long_run_miles * 0.25, 2.0, 4.0))
            easy_miles = round_to_half_mile(long_run_miles - finish_miles)
            return {
                "miles": long_run_miles,
                "style": "steady_finish",
                "stress": round(long_run_miles * 0.9, 1),
                "session": (
                    f"{long_run_miles:.1f} mi long run: {easy_miles:.1f} mi easy @ {easy_pace}/mi, "
                    f"then {finish_miles:.1f} mi around 85% ({steady_pace}/mi)"
                ),
            }

        if stress_tier == "moderate":
            finish_miles = round_to_half_mile(clamp(long_run_miles * 0.18, 1.5, 3.0))
            easy_miles = round_to_half_mile(long_run_miles - finish_miles)
            return {
                "miles": long_run_miles,
                "style": "light_steady_finish",
                "stress": round(long_run_miles * 0.84, 1),
                "session": (
                    f"{long_run_miles:.1f} mi long run: {easy_miles:.1f} mi easy @ {easy_pace}/mi, "
                    f"finish last {finish_miles:.1f} mi around 85% ({steady_pace}/mi)"
                ),
            }

        return {
            "miles": long_run_miles,
            "style": "easy",
            "stress": round(long_run_miles * 0.78, 1),
            "session": f"{long_run_miles:.1f} mi long run mostly easy @ {easy_pace}/mi",
        }

    if phase == "race-supportive":
        if 90 not in {primary_band, support_band} and stress_tier in {"low", "moderate"}:
            quality_miles = round_to_half_mile(clamp(long_run_miles * 0.25, 2.0, 4.5))
            easy_miles = round_to_half_mile(long_run_miles - quality_miles)
            return {
                "miles": long_run_miles,
                "style": "supportive_90",
                "stress": round(long_run_miles * 0.98, 1),
                "session": (
                    f"{long_run_miles:.1f} mi long run: {easy_miles:.1f} mi easy @ {easy_pace}/mi, "
                    f"then {quality_miles:.1f} mi around 90% ({supportive_pace}/mi)"
                ),
            }

        finish_miles = round_to_half_mile(clamp(long_run_miles * 0.15, 1.5, 3.0))
        easy_miles = round_to_half_mile(long_run_miles - finish_miles)
        return {
            "miles": long_run_miles,
            "style": "steady_finish",
            "stress": round(long_run_miles * 0.88, 1),
            "session": (
                f"{long_run_miles:.1f} mi long run: {easy_miles:.1f} mi easy @ {easy_pace}/mi, "
                f"finish last {finish_miles:.1f} mi around 85% ({steady_pace}/mi)"
            ),
        }

    if 90 not in {primary_band, support_band} and stress_tier == "low":
        quality_miles = round_to_half_mile(clamp(long_run_miles * 0.15, 1.0, 2.5))
        easy_miles = round_to_half_mile(long_run_miles - quality_miles)
        return {
            "miles": long_run_miles,
            "style": "short_90_finish",
            "stress": round(long_run_miles * 0.9, 1),
            "session": (
                f"{long_run_miles:.1f} mi long run: {easy_miles:.1f} mi mostly easy @ {easy_pace}/mi, "
                f"then {quality_miles:.1f} mi around 90% ({supportive_pace}/mi)"
            ),
        }

    return {
        "miles": long_run_miles,
        "style": "easy",
        "stress": round(long_run_miles * 0.8, 1),
        "session": f"{long_run_miles:.1f} mi long run mostly easy @ {easy_pace}/mi",
    }


def _recovery_templates(
    phase: str,
    primary_stress_tier: str,
    support_stress_tier: str,
    weekly_stress_tier: str,
    long_run_style: str,
) -> Dict[str, str]:
    if phase == "general":
        monday = "easy_to_steady" if weekly_stress_tier == "low" else "easy"
        wednesday = "easy" if primary_stress_tier == "low" else "very_easy"
        friday = "easy_to_steady" if support_stress_tier == "low" and weekly_stress_tier != "high" else "easy"
        sunday = "easy" if long_run_style != "steady_finish" else "very_easy"
        return {
            "Monday": monday,
            "Wednesday": wednesday,
            "Friday": friday,
            "Sunday": sunday,
        }

    if phase == "race-supportive":
        return {
            "Monday": "easy",
            "Wednesday": "very_easy" if primary_stress_tier in {"high", "very_high"} else "easy",
            "Friday": "very_easy" if support_stress_tier in {"high", "very_high"} else "easy",
            "Sunday": "off" if weekly_stress_tier == "very_high" else "very_easy",
        }

    sunday = "off" if weekly_stress_tier in {"high", "very_high"} else "very_easy"
    monday = "very_easy" if long_run_style != "easy" else "easy"
    return {
        "Monday": monday,
        "Wednesday": "very_easy",
        "Friday": "very_easy",
        "Sunday": sunday,
    }


def _build_aerobic_day(style: str, base_easy_miles: float, ladder: Dict[int, Dict[str, float | str]]) -> Dict[str, object]:
    miles = round_to_half_mile(base_easy_miles * DAY_STYLE_MULTIPLIERS[style])
    easy_pace = ladder[80]["pace_per_mile"]
    steady_pace = ladder[85]["pace_per_mile"]

    if style == "off":
        return {"miles": 0.0, "session": "Off or 20-30 min walk / mobility"}

    if style == "shakeout":
        return {"miles": miles, "session": f"{miles:.1f} mi shakeout @ {easy_pace}/mi"}

    if style == "very_easy":
        return {"miles": miles, "session": f"{miles:.1f} mi very easy @ {easy_pace}/mi"}

    if style == "easy_strides":
        return {
            "miles": miles,
            "session": f"{miles:.1f} mi easy @ {easy_pace}/mi + 4-6 x 20 sec relaxed strides",
        }

    if style == "easy_to_steady":
        finish_miles = round_to_half_mile(clamp(miles * 0.25, 1.0, 2.0))
        easy_miles = round_to_half_mile(max(0.0, miles - finish_miles))
        return {
            "miles": miles,
            "session": (
                f"{miles:.1f} mi aerobic run: {easy_miles:.1f} mi easy @ {easy_pace}/mi, "
                f"finish {finish_miles:.1f} mi around 85% ({steady_pace}/mi)"
            ),
        }

    if style == "steady":
        return {"miles": miles, "session": f"{miles:.1f} mi steady around 85% ({steady_pace}/mi)"}

    return {"miles": miles, "session": f"{miles:.1f} mi easy @ {easy_pace}/mi"}
