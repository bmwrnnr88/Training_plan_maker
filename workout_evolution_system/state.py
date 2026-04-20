from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List

from workout_evolution_system.event_profiles import default_states_for_event
from workout_evolution_system.pace_ladder import PACE_BANDS
from workout_evolution_system.progression import recommend_rest_seconds
from workout_evolution_system.utils import clean_number


def default_workout_states(
    goal_event: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    return deepcopy(default_states_for_event(goal_event, ladder))


def states_to_rows(states: Dict[int, Dict[str, object]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for band in PACE_BANDS:
        state = states[band]
        current = state["current"]

        rows.append(
            {
                "band": band,
                "zone": state["zone"],
                "pace_per_mile": state["pace"],
                "workout_type": current.get("type", "continuous"),
                "reps": int(current.get("reps", 0) or 0),
                "distance_m": int(current.get("distance_m", 0) or 0),
                "distance_miles": float(current.get("distance_miles", 0.0) or 0.0),
                "rest_sec": int(current.get("rest_sec", 0) or 0),
                "recent_sessions_21d": int(state.get("recent_sessions_21d", 0) or 0),
                "days_since_last": int(state.get("days_since_last", 7) or 7),
            }
        )

    return rows


def rows_to_states(
    rows: Iterable[Dict[str, object]],
    goal_event: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    defaults = default_workout_states(goal_event, ladder)
    states: Dict[int, Dict[str, object]] = {}

    for row in rows:
        band = int(clean_number(row.get("band"), 0))
        if band not in defaults:
            continue

        workout_type = str(row.get("workout_type", "continuous") or "continuous")
        current: Dict[str, object] = {"type": workout_type}

        if workout_type == "interval":
            current["reps"] = max(1, int(round(clean_number(row.get("reps"), 1))))
            current["distance_m"] = max(100, int(round(clean_number(row.get("distance_m"), 100))))

            rest_value = int(round(clean_number(row.get("rest_sec"), 0)))
            if rest_value <= 0:
                pace_seconds = ladder[band]["seconds_per_mile"]
                work_duration = pace_seconds * (current["distance_m"] / 1609.344)
                rest_value = recommend_rest_seconds(band, work_duration)
            current["rest_sec"] = rest_value
        elif workout_type == "broken_tempo":
            current["reps"] = max(2, int(round(clean_number(row.get("reps"), 2))))
            current["distance_miles"] = max(0.5, clean_number(row.get("distance_miles"), 4.0))

            rest_value = int(round(clean_number(row.get("rest_sec"), 0)))
            if rest_value <= 0:
                pace_seconds = ladder[band]["seconds_per_mile"]
                work_duration = pace_seconds * current["distance_miles"]
                rest_value = recommend_rest_seconds(band, work_duration)
            current["rest_sec"] = rest_value
        else:
            current["type"] = "continuous"
            current["distance_miles"] = max(0.5, clean_number(row.get("distance_miles"), 4.0))

        states[band] = {
            "band": band,
            "pace": ladder[band]["pace_per_mile"],
            "zone": str(row.get("zone", defaults[band]["zone"])),
            "current": current,
            "recent_sessions_21d": max(0, int(round(clean_number(row.get("recent_sessions_21d"), defaults[band].get("recent_sessions_21d", 0))))),
            "days_since_last": max(0, int(round(clean_number(row.get("days_since_last"), defaults[band].get("days_since_last", 7))))),
        }

    for band, state in defaults.items():
        states.setdefault(band, state)

    return states
