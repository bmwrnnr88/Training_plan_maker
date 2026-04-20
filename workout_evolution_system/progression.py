from __future__ import annotations

from copy import deepcopy
from typing import Dict

from workout_evolution_system.event_profiles import progression_paths
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
    return clamp(_state_progress_value(state), 0.0, 1.0)


def progress_ratio_to_peak(
    state: Dict[str, object],
    peak_state: Dict[str, object],
) -> float:
    peak_value = max(0.01, _state_progress_value(peak_state))
    return clamp(_state_progress_value(state) / peak_value, 0.0, 1.0)


def progress_value_to_peak(
    state: Dict[str, object],
    peak_state: Dict[str, object],
) -> float:
    peak_value = max(0.01, _state_progress_value(peak_state))
    return _state_progress_value(state) / peak_value


def next_progression_for_band(
    state: Dict[str, object],
    ladder: Dict[int, Dict[str, float | str]],
    goal_event: str,
    allow_extension: bool = False,
) -> Dict[str, object]:
    band = int(state["band"])
    path = progression_paths(goal_event, ladder)[band]
    current_index = _nearest_progression_index(state, path)

    if current_index < len(path) - 1:
        next_state = deepcopy(state)
        next_state["current"] = deepcopy(path[current_index + 1])
        return {
            "state": next_state,
            "changed": True,
            "reason": "Next step progresses toward the appendix peak workout for this goal race.",
        }

    if not allow_extension:
        peak_state = deepcopy(state)
        peak_state["current"] = deepcopy(path[-1])
        return {
            "state": peak_state,
            "changed": False,
            "reason": "This band is already at the current peak target for the selected goal race.",
        }

    extended_state = deepcopy(state)
    extended_state["current"] = _extend_beyond_peak(path[-1], band)
    return {
        "state": extended_state,
        "changed": True,
        "reason": "Peak target reached; extension keeps the pace fixed and grows continuity or duration.",
    }


def peak_state_for_band(
    goal_event: str,
    band: int,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[str, object]:
    peak_current = deepcopy(progression_paths(goal_event, ladder)[band][-1])
    return {
        "band": band,
        "pace": ladder[band]["pace_per_mile"],
        "zone": str(ladder[band]["zone"]),
        "current": peak_current,
    }


def _nearest_step(value: int, steps: list[int]) -> int:
    return min(steps, key=lambda step: abs(step - value))


def _state_progress_value(state: Dict[str, object]) -> float:
    current = state["current"]
    workout_type = current["type"]
    value = workout_volume_miles(state)

    if workout_type == "continuous":
        value += 0.45
        value += float(current.get("distance_miles", 0.0)) * 0.04
        return value

    if workout_type == "broken_tempo":
        value += 0.3
        value += float(current.get("distance_miles", 0.0)) * 0.03
        return value

    rep_distance_m = int(current.get("distance_m", 0))
    rep_miles = meters_to_miles(rep_distance_m)
    reps = int(current.get("reps", 0))
    rest_sec = int(current.get("rest_sec", 60))
    density_bonus = clamp(180 / max(rest_sec, 30), 0.7, 1.25)
    return value + (rep_miles * 0.4) + (reps * 0.03) + ((density_bonus - 1.0) * 0.35)


def _nearest_progression_index(state: Dict[str, object], path: list[Dict[str, object]]) -> int:
    state_value = _state_progress_value(state)
    path_values = [_state_progress_value({"band": state["band"], "current": step}) for step in path]

    best_index = 0
    for i, value in enumerate(path_values):
        if state_value >= value * 0.98:
            best_index = i

    return best_index


def _extend_beyond_peak(peak_current: Dict[str, object], band: int) -> Dict[str, object]:
    current = deepcopy(peak_current)

    if current["type"] == "continuous":
        current["distance_miles"] = round_to_half_mile(float(current.get("distance_miles", 0.0)) + 1.0)
        return current

    if current["type"] == "broken_tempo":
        current["distance_miles"] = round_to_half_mile(float(current.get("distance_miles", 0.0)) + 0.5)
        return current

    if band == 100:
        current["type"] = "continuous"
        current.pop("reps", None)
        current.pop("distance_m", None)
        current.pop("rest_sec", None)
        current["distance_miles"] = max(3.0, round_to_half_mile(workout_volume_miles({"band": band, "current": peak_current}) * 0.65))
        return current

    if band in {105, 110, 115}:
        current["reps"] = int(current.get("reps", 0)) + (2 if band >= 110 else 1)
        return current

    current["distance_miles"] = round_to_half_mile(float(current.get("distance_miles", 0.0)) + 1.0)
    return current
