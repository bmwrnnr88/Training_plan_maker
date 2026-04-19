from __future__ import annotations

from copy import deepcopy
from typing import Dict

from workout_evolution_system.utils import clamp, meters_to_miles, round_to_half_mile, seconds_to_clock


REST_MULTIPLIER_RANGES = {
    "threshold": (0.25, 0.4),
    "race": (0.4, 0.6),
    "cv": (0.5, 0.8),
    "vo2": (0.8, 1.2),
    "speed": (2.0, 4.0),
}

DEFAULT_REST_MULTIPLIERS = {
    "threshold": 0.33,
    "race": 0.5,
    "cv": 0.65,
    "vo2": 1.0,
    "speed": 3.0,
}

RACE_DISTANCE_STEPS = [1000, 1200, 1609, 2000]
CV_DISTANCE_STEPS = [600, 800, 1000]
SPEED_REP_TARGETS = {110: 12, 115: 10}
ENDURANCE_TARGETS = {80: 14.0, 85: 12.0, 90: 10.0, 95: 8.0}


def _rest_family_for_band(band: int) -> str:
    if band == 95:
        return "threshold"
    if band == 100:
        return "race"
    if band == 105:
        return "cv"
    if band >= 110:
        return "speed"
    return "threshold"


def recommend_rest_seconds(band: int, work_duration_seconds: float) -> int:
    family = _rest_family_for_band(band)
    multiplier = DEFAULT_REST_MULTIPLIERS[family]
    raw_rest = work_duration_seconds * multiplier
    return int(round(clamp(raw_rest, 30, 300)))


def workout_volume_miles(state: Dict[str, object]) -> float:
    current = state["current"]
    workout_type = current["type"]

    if workout_type == "continuous":
        return float(current.get("distance_miles", 0.0))

    if workout_type == "broken_tempo":
        reps = int(current.get("reps", 2))
        distance_miles = float(current.get("distance_miles", 0.0))
        return reps * distance_miles

    reps = int(current.get("reps", 0))
    distance_m = float(current.get("distance_m", 0.0))
    return reps * meters_to_miles(distance_m)


def describe_workout(state: Dict[str, object], ladder: Dict[int, Dict[str, float | str]]) -> str:
    band = int(state["band"])
    current = state["current"]
    workout_type = current["type"]
    pace = ladder[band]["pace_per_mile"]

    if workout_type == "continuous":
        return f"{current['distance_miles']:.1f} mi continuous @ {pace}/mi"

    if workout_type == "broken_tempo":
        reps = int(current.get("reps", 2))
        rest = int(current.get("rest_sec", 0))
        return (
            f"{reps} x {current['distance_miles']:.1f} mi @ {pace}/mi / "
            f"{seconds_to_clock(rest)} rest"
        )

    reps = int(current["reps"])
    distance_m = int(current["distance_m"])
    rest = int(current.get("rest_sec", 0))
    return f"{reps} x {distance_m}m @ {pace}/mi / {seconds_to_clock(rest)} rest"


def progress_ratio_for_band(state: Dict[str, object]) -> float:
    band = int(state["band"])
    current = state["current"]
    workout_type = current["type"]

    if band in ENDURANCE_TARGETS:
        target = ENDURANCE_TARGETS[band]
        if workout_type == "broken_tempo":
            return 1.0
        return clamp(float(current.get("distance_miles", 0.0)) / target, 0.0, 1.0)

    if band == 100:
        if workout_type == "continuous":
            return clamp(0.85 + ((float(current.get("distance_miles", 3.0)) - 3.0) / 2.0) * 0.15, 0.0, 1.0)

        reps = int(current.get("reps", 0))
        distance_m = int(current.get("distance_m", 1000))
        distance_index = RACE_DISTANCE_STEPS.index(_nearest_step(distance_m, RACE_DISTANCE_STEPS))
        step_progress = distance_index / (len(RACE_DISTANCE_STEPS) - 1)
        rep_progress = clamp(reps / 6.0, 0.0, 1.0)
        return clamp((step_progress * 0.65) + (rep_progress * 0.35), 0.0, 0.95)

    if band == 105:
        reps = int(current.get("reps", 0))
        distance_m = int(current.get("distance_m", 600))
        distance_index = CV_DISTANCE_STEPS.index(_nearest_step(distance_m, CV_DISTANCE_STEPS))
        distance_progress = distance_index / (len(CV_DISTANCE_STEPS) - 1)
        rep_progress = clamp(reps / 8.0, 0.0, 1.0)
        rest_progress = 0.0
        if distance_index == len(CV_DISTANCE_STEPS) - 1:
            rest_sec = int(current.get("rest_sec", 300))
            rest_progress = clamp((300 - rest_sec) / 270.0, 0.0, 1.0)
        return clamp((distance_progress * 0.45) + (rep_progress * 0.4) + (rest_progress * 0.15), 0.0, 1.0)

    if band in SPEED_REP_TARGETS:
        reps = int(current.get("reps", 0))
        return clamp(reps / SPEED_REP_TARGETS[band], 0.0, 1.0)

    return 0.0


def next_progression_for_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    band = int(state["band"])
    current = state["current"]

    if band in {80, 85, 90, 95}:
        return _progress_endurance_band(state, ladder)
    if band == 100:
        return _progress_race_band(state, ladder)
    if band == 105:
        return _progress_cv_band(state, ladder)
    return _progress_speed_band(state, ladder)


def _progress_endurance_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    band = int(state["band"])
    current = deepcopy(state["current"])
    target = ENDURANCE_TARGETS[band]

    if current["type"] == "broken_tempo":
        return {
            "state": deepcopy(state),
            "changed": False,
            "reason": "This band is already at its broken-tempo cap.",
        }

    current_distance = float(current.get("distance_miles", 0.0))

    if band == 95 and current_distance >= 8.0:
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "broken_tempo",
            "reps": 2,
            "distance_miles": 4.0,
            "rest_sec": recommend_rest_seconds(
                band=95,
                work_duration_seconds=ladder[95]["seconds_per_mile"] * 4.0,
            ),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "Threshold work capped at 8 continuous miles, so the next step is a broken tempo.",
        }

    if band == 90 and current_distance >= target:
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "broken_tempo",
            "reps": 2,
            "distance_miles": 5.0,
            "rest_sec": recommend_rest_seconds(
                band=90,
                work_duration_seconds=ladder[90]["seconds_per_mile"] * 5.0,
            ),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "Supportive endurance has hit its continuous cap, so the next step is a broken steady session.",
        }

    if current_distance >= target:
        return {
            "state": deepcopy(state),
            "changed": False,
            "reason": "This band is already at its current continuous target.",
        }

    next_state = deepcopy(state)
    next_distance = min(target, current_distance + 1.0)
    next_state["current"] = {
        "type": "continuous",
        "distance_miles": next_distance,
    }

    return {
        "state": next_state,
        "changed": True,
        "reason": "Progression comes from extending the continuous run by one mile.",
    }


def _progress_race_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    current = deepcopy(state["current"])

    if current["type"] == "continuous":
        current_distance = float(current.get("distance_miles", 3.0))
        if current_distance >= 5.0:
            return {
                "state": deepcopy(state),
                "changed": False,
                "reason": "Race-pace work is already at the 5-mile continuous cap.",
            }

        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "continuous",
            "distance_miles": min(5.0, current_distance + 1.0),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "The next step is more continuity at race pace.",
        }

    reps = int(current.get("reps", 4))
    distance_m = _nearest_step(int(current.get("distance_m", 1000)), RACE_DISTANCE_STEPS)

    if reps < 6:
        next_reps = reps + 1
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "interval",
            "reps": next_reps,
            "distance_m": distance_m,
            "rest_sec": recommend_rest_seconds(
                band=100,
                work_duration_seconds=ladder[100]["seconds_per_mile"] * meters_to_miles(distance_m),
            ),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "Race-pace progression adds reps until six are in place.",
        }

    distance_index = RACE_DISTANCE_STEPS.index(distance_m)
    if distance_index < len(RACE_DISTANCE_STEPS) - 1:
        next_distance = RACE_DISTANCE_STEPS[distance_index + 1]
        next_reps = 5 if next_distance <= 1200 else 4
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "interval",
            "reps": next_reps,
            "distance_m": next_distance,
            "rest_sec": recommend_rest_seconds(
                band=100,
                work_duration_seconds=ladder[100]["seconds_per_mile"] * meters_to_miles(next_distance),
            ),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "Race-pace progression now extends rep length: 1000m -> 1200m -> mile -> 2k.",
        }

    next_state = deepcopy(state)
    next_state["current"] = {
        "type": "continuous",
        "distance_miles": 3.0,
    }
    return {
        "state": next_state,
        "changed": True,
        "reason": "Once the interval ladder reaches 2k reps, the next step is continuous race-pace work.",
    }


def _progress_cv_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    current = deepcopy(state["current"])
    reps = int(current.get("reps", 6))
    distance_m = _nearest_step(int(current.get("distance_m", 600)), CV_DISTANCE_STEPS)
    rest_sec = int(current.get("rest_sec", 0)) or recommend_rest_seconds(
        band=105,
        work_duration_seconds=ladder[105]["seconds_per_mile"] * meters_to_miles(distance_m),
    )

    if reps < 8:
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "interval",
            "reps": reps + 1,
            "distance_m": distance_m,
            "rest_sec": rest_sec,
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "CV progression adds reps first, up to eight.",
        }

    distance_index = CV_DISTANCE_STEPS.index(distance_m)
    if distance_index < len(CV_DISTANCE_STEPS) - 1:
        next_distance = CV_DISTANCE_STEPS[distance_index + 1]
        next_state = deepcopy(state)
        next_state["current"] = {
            "type": "interval",
            "reps": 6,
            "distance_m": next_distance,
            "rest_sec": recommend_rest_seconds(
                band=105,
                work_duration_seconds=ladder[105]["seconds_per_mile"] * meters_to_miles(next_distance),
            ),
        }
        return {
            "state": next_state,
            "changed": True,
            "reason": "After eight reps, CV progression lengthens the rep: 600m -> 800m -> 1k.",
        }

    next_rest = max(30, rest_sec - 15)
    if next_rest == rest_sec:
        return {
            "state": deepcopy(state),
            "changed": False,
            "reason": "CV work is already at the minimum rest floor.",
        }

    next_state = deepcopy(state)
    next_state["current"] = {
        "type": "interval",
        "reps": reps,
        "distance_m": distance_m,
        "rest_sec": next_rest,
    }
    return {
        "state": next_state,
        "changed": True,
        "reason": "Once reps and rep length are built, CV progression tightens density by trimming rest.",
    }


def _progress_speed_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    band = int(state["band"])
    current = deepcopy(state["current"])
    reps = int(current.get("reps", 0))
    distance_m = int(current.get("distance_m", 200))
    target_reps = SPEED_REP_TARGETS[band]
    rest_sec = recommend_rest_seconds(
        band=band,
        work_duration_seconds=ladder[band]["seconds_per_mile"] * meters_to_miles(distance_m),
    )

    next_state = deepcopy(state)
    next_state["current"] = {
        "type": "interval",
        "reps": min(target_reps, reps + 1),
        "distance_m": distance_m,
        "rest_sec": rest_sec,
    }

    if reps >= target_reps:
        return {
            "state": next_state,
            "changed": False,
            "reason": "Speed work is already at the current rep target; keep full recovery and stay interval-based.",
        }

    return {
        "state": next_state,
        "changed": True,
        "reason": "Speed progression only adds reps and keeps full recovery; it never converts to continuous running.",
    }


def _nearest_step(value: int, steps: list[int]) -> int:
    return min(steps, key=lambda step: abs(step - value))
