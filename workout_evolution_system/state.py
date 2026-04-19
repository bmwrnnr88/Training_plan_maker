from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List

from workout_evolution_system.pace_ladder import PACE_BANDS
from workout_evolution_system.progression import recommend_rest_seconds
from workout_evolution_system.utils import clean_number


def default_workout_states(
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    states: Dict[int, Dict[str, object]] = {
        80: {
            "band": 80,
            "pace": ladder[80]["pace_per_mile"],
            "zone": "easy",
            "current": {"type": "continuous", "distance_miles": 6.0},
            "target": "Build aerobic support and hold easy mileage around this pace.",
        },
        85: {
            "band": 85,
            "pace": ladder[85]["pace_per_mile"],
            "zone": "steady",
            "current": {"type": "continuous", "distance_miles": 8.0},
            "target": "Progress steady running toward 12 miles.",
        },
        90: {
            "band": 90,
            "pace": ladder[90]["pace_per_mile"],
            "zone": "supportive_endurance",
            "current": {"type": "continuous", "distance_miles": 6.0},
            "target": "Progress continuous work toward 10 miles, then 2 x 5 miles.",
        },
        95: {
            "band": 95,
            "pace": ladder[95]["pace_per_mile"],
            "zone": "threshold",
            "current": {"type": "continuous", "distance_miles": 5.0},
            "target": "Increase by 1 mile each step to 8 miles, then 2 x 4 miles.",
        },
        100: {
            "band": 100,
            "pace": ladder[100]["pace_per_mile"],
            "zone": "race",
            "current": {
                "type": "interval",
                "reps": 5,
                "distance_m": 1000,
                "rest_sec": recommend_rest_seconds(
                    band=100,
                    work_duration_seconds=(ladder[100]["seconds_per_mile"] * (1000 / 1609.344)),
                ),
            },
            "target": "Grow to 6 reps, then 1200m, mile, 2k, and eventually 3-5 miles continuous.",
        },
        105: {
            "band": 105,
            "pace": ladder[105]["pace_per_mile"],
            "zone": "cv",
            "current": {
                "type": "interval",
                "reps": 6,
                "distance_m": 600,
                "rest_sec": recommend_rest_seconds(
                    band=105,
                    work_duration_seconds=(ladder[105]["seconds_per_mile"] * (600 / 1609.344)),
                ),
            },
            "target": "Grow to 8 reps, then 800m, 1k, then shorten the rest.",
        },
        110: {
            "band": 110,
            "pace": ladder[110]["pace_per_mile"],
            "zone": "speed",
            "current": {
                "type": "interval",
                "reps": 8,
                "distance_m": 300,
                "rest_sec": recommend_rest_seconds(
                    band=110,
                    work_duration_seconds=(ladder[110]["seconds_per_mile"] * (300 / 1609.344)),
                ),
            },
            "target": "Increase reps gradually, keep full recovery, stay interval-based.",
        },
        115: {
            "band": 115,
            "pace": ladder[115]["pace_per_mile"],
            "zone": "speed",
            "current": {
                "type": "interval",
                "reps": 6,
                "distance_m": 200,
                "rest_sec": recommend_rest_seconds(
                    band=115,
                    work_duration_seconds=(ladder[115]["seconds_per_mile"] * (200 / 1609.344)),
                ),
            },
            "target": "Increase reps gradually, keep full recovery, stay interval-based.",
        },
    }

    return deepcopy(states)


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
                "target": state.get("target", ""),
            }
        )

    return rows


def rows_to_states(
    rows: Iterable[Dict[str, object]],
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    defaults = default_workout_states(ladder)
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
            "target": str(row.get("target", defaults[band]["target"])),
        }

    for band, state in defaults.items():
        states.setdefault(band, state)

    return states
