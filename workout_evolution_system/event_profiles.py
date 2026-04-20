from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from workout_evolution_system.utils import round_to_half_mile


EVENT_LABELS = {
    "5k": "5K",
    "10k": "10K",
    "half_marathon": "Half Marathon",
    "marathon": "Marathon",
}


EVENT_PHASE_BANDS = {
    "5k": {
        "general": [90, 100, 105, 110, 85],
        "race-supportive": [90, 95, 100, 105, 110],
        "race-specific": [95, 100, 105, 110, 90],
    },
    "10k": {
        "general": [90, 105, 100, 110, 85],
        "race-supportive": [90, 95, 100, 105, 110],
        "race-specific": [95, 100, 105, 90, 110],
    },
    "half_marathon": {
        "general": [85, 90, 95, 105],
        "race-supportive": [90, 95, 100, 105, 85],
        "race-specific": [95, 100, 90, 105],
    },
    "marathon": {
        "general": [85, 90, 95, 105],
        "race-supportive": [90, 95, 100, 105, 85],
        "race-specific": [95, 100, 90, 105],
    },
}

EVENT_PHASE_WEIGHTS = {
    "5k": {
        "general": {85: 1.1, 90: 1.2, 100: 1.0, 105: 0.95, 110: 0.8},
        "race-supportive": {90: 1.15, 95: 1.15, 100: 1.05, 105: 1.0, 110: 0.9},
        "race-specific": {90: 0.9, 95: 1.15, 100: 1.2, 105: 1.1, 110: 0.95},
    },
    "10k": {
        "general": {85: 1.15, 90: 1.25, 100: 0.95, 105: 0.9, 110: 0.72},
        "race-supportive": {90: 1.2, 95: 1.15, 100: 1.0, 105: 0.95, 110: 0.82},
        "race-specific": {90: 0.92, 95: 1.2, 100: 1.18, 105: 1.08, 110: 0.82},
    },
    "half_marathon": {
        "general": {85: 1.2, 90: 1.2, 95: 1.05, 105: 0.8},
        "race-supportive": {85: 0.95, 90: 1.15, 95: 1.15, 100: 1.05, 105: 0.85},
        "race-specific": {90: 1.0, 95: 1.2, 100: 1.12, 105: 0.9},
    },
    "marathon": {
        "general": {85: 1.25, 90: 1.15, 95: 0.95, 105: 0.72},
        "race-supportive": {85: 1.0, 90: 1.18, 95: 1.15, 100: 0.98, 105: 0.8},
        "race-specific": {90: 1.12, 95: 1.22, 100: 1.05, 105: 0.82},
    },
}


PHASE_LENGTH_HINTS = {
    "5k": {"specific_ratio": 0.32, "specific_min": 4, "support_ratio": 0.22, "support_min": 3},
    "10k": {"specific_ratio": 0.35, "specific_min": 4, "support_ratio": 0.25, "support_min": 3},
    "half_marathon": {"specific_ratio": 0.38, "specific_min": 5, "support_ratio": 0.24, "support_min": 3},
    "marathon": {"specific_ratio": 0.42, "specific_min": 6, "support_ratio": 0.24, "support_min": 4},
}


def phase_from_weeks(goal_event: str, weeks_to_goal: int) -> str:
    hints = PHASE_LENGTH_HINTS[goal_event]
    specific = max(hints["specific_min"], round(weeks_to_goal * hints["specific_ratio"]))
    support = max(hints["support_min"], round(weeks_to_goal * hints["support_ratio"]))

    if weeks_to_goal <= specific:
        return "race-specific"
    if weeks_to_goal <= specific + support:
        return "race-supportive"
    return "general"


def candidate_bands(goal_event: str, phase: str) -> List[int]:
    return EVENT_PHASE_BANDS[goal_event][phase]


def band_weight(goal_event: str, phase: str, band: int) -> float:
    return EVENT_PHASE_WEIGHTS.get(goal_event, {}).get(phase, {}).get(band, 1.0)


def progression_paths(
    goal_event: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, List[Dict[str, object]]]:
    return {
        "5k": _five_k_paths,
        "10k": _ten_k_paths,
        "half_marathon": _half_paths,
        "marathon": _marathon_paths,
    }[goal_event](ladder)


def default_states_for_event(
    goal_event: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    paths = progression_paths(goal_event, ladder)
    states: Dict[int, Dict[str, object]] = {}

    for band, path in paths.items():
        states[band] = {
            "band": band,
            "pace": ladder[band]["pace_per_mile"],
            "zone": str(ladder[band]["zone"]),
            "current": deepcopy(path[0]),
            "recent_sessions_21d": 0,
            "days_since_last": 7,
        }

    return states


def peak_states_for_event(
    goal_event: str,
    ladder: Dict[int, Dict[str, float | str]],
) -> Dict[int, Dict[str, object]]:
    paths = progression_paths(goal_event, ladder)
    return {
        band: {
            "band": band,
            "pace": ladder[band]["pace_per_mile"],
            "zone": str(ladder[band]["zone"]),
            "current": deepcopy(path[-1]),
        }
        for band, path in paths.items()
    }


def _continuous(distance_miles: float) -> Dict[str, object]:
    return {"type": "continuous", "distance_miles": round_to_half_mile(distance_miles)}


def _interval(reps: int, distance_m: int, rest_sec: int) -> Dict[str, object]:
    return {"type": "interval", "reps": reps, "distance_m": distance_m, "rest_sec": rest_sec}


def _five_k_paths(_: Dict[int, Dict[str, float | str]]) -> Dict[int, List[Dict[str, object]]]:
    return {
        80: [_continuous(8), _continuous(10), _continuous(12)],
        85: [_continuous(5), _continuous(7), _continuous(8)],
        90: [_continuous(4), _continuous(5), _continuous(6)],
        95: [_continuous(2.5), _continuous(3.0), _continuous(3.5), _continuous(4.0)],
        100: [
            _interval(5, 800, 180),
            _interval(6, 800, 180),
            _interval(5, 1000, 180),
            _interval(5, 1200, 180),
            _interval(6, 1200, 180),
        ],
        105: [
            _interval(6, 400, 75),
            _interval(8, 400, 60),
            _interval(8, 500, 60),
            _interval(10, 500, 60),
        ],
        110: [
            _interval(8, 200, 90),
            _interval(12, 200, 75),
            _interval(16, 200, 75),
        ],
        115: [
            _interval(8, 200, 150),
            _interval(10, 200, 150),
            _interval(12, 200, 150),
        ],
    }


def _ten_k_paths(_: Dict[int, Dict[str, float | str]]) -> Dict[int, List[Dict[str, object]]]:
    return {
        80: [_continuous(10), _continuous(12), _continuous(14)],
        85: [_continuous(8), _continuous(10), _continuous(12)],
        90: [_continuous(6), _continuous(8), _continuous(9), _continuous(10)],
        95: [_continuous(4), _continuous(5), _continuous(6), _continuous(7)],
        100: [
            _interval(5, 1000, 120),
            _interval(6, 1000, 120),
            _interval(5, 1200, 150),
            _interval(4, 1609, 180),
            _interval(4, 2000, 180),
            _interval(5, 2000, 180),
        ],
        105: [
            _interval(6, 600, 90),
            _interval(8, 600, 90),
            _interval(6, 800, 120),
            _interval(6, 1000, 240),
        ],
        110: [
            _interval(6, 300, 120),
            _interval(8, 300, 120),
            _interval(6, 400, 120),
            _interval(8, 500, 105),
            _interval(10, 500, 105),
        ],
        115: [
            _interval(8, 200, 120),
            _interval(10, 200, 120),
            _interval(12, 200, 120),
            _interval(16, 200, 120),
        ],
    }


def _half_paths(_: Dict[int, Dict[str, float | str]]) -> Dict[int, List[Dict[str, object]]]:
    return {
        80: [_continuous(10), _continuous(12), _continuous(14)],
        85: [_continuous(10), _continuous(12), _continuous(14)],
        90: [_continuous(10), _continuous(12), _continuous(14)],
        95: [_continuous(8), _continuous(10), _continuous(12)],
        100: [
            _interval(4, 3000, 180),
            _interval(5, 3000, 180),
            _interval(6, 3000, 180),
        ],
        105: [
            _interval(4, 1609, 180),
            _interval(5, 1609, 180),
            _interval(5, 2000, 180),
        ],
        110: [
            _interval(6, 800, 120),
            _interval(8, 800, 120),
        ],
        115: [
            _interval(8, 300, 75),
            _interval(10, 300, 75),
            _interval(12, 300, 75),
        ],
    }


def _marathon_paths(_: Dict[int, Dict[str, float | str]]) -> Dict[int, List[Dict[str, object]]]:
    return {
        80: [_continuous(14), _continuous(16), _continuous(18)],
        85: [_continuous(14), _continuous(16), _continuous(18)],
        90: [_continuous(14), _continuous(16), _continuous(18)],
        95: [_continuous(12), _continuous(14), _continuous(16)],
        100: [
            _interval(4, 3000, 180),
            _interval(5, 3000, 180),
            _interval(5, 4000, 180),
        ],
        105: [
            _interval(6, 1000, 180),
            _interval(8, 1000, 180),
            _interval(10, 1000, 180),
        ],
        110: [
            _interval(2, 3000, 180),
            _interval(3, 3000, 180),
        ],
        115: [
            _interval(6, 800, 120),
            _interval(8, 800, 120),
        ],
    }
