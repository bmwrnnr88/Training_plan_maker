from __future__ import annotations

from typing import Dict, List, Tuple


def _band_pace(paces: Dict[int, Dict[str, str]], pct: int) -> str:
    return paces[pct]["pace_per_mile"]


def _band_km_pace(paces: Dict[int, Dict[str, str]], pct: int) -> str:
    return paces[pct]["pace_per_km"]


# -------------------------------------------------------------------
# FINAL TARGET WORKOUTS
# These are the "culminating" / recommended workouts the plan builds toward.
# They are adapted from the appendix in the comprehensive overview article,
# plus the more detailed 10k article and printable 10k schedule where helpful.
# -------------------------------------------------------------------

FINAL_TARGETS: Dict[str, Dict[int, str]] = {
    "800m": {
        80: "4–5 x 1 km @ 80% / 2 min jog or 3 mi continuous @ 80%",
        85: "5 x 600m @ 85% / 3–4 min walk/jog",
        90: "4–5 x 500m @ 90% / 4–5 min walk/jog",
        95: "3–4 x 600m @ 95% / 4–5 min walk/jog",
        100: "3 x 500m @ 100% / 6–8 min walk/jog",
        105: "6 x 300m @ 105% / 2–3 min walk/jog",
        110: "10–12 x 200m @ 110% / 2–3 min walk/jog",
        115: "6–10 x 60m @ 115% / full walk recovery",
    },
    "1500m": {
        80: "6–8 x 1 km @ 80% / 1–2 min jog or 3–5 mi @ 80%",
        85: "5–7 x 1 km @ 85% / 1.5–3 min walk/jog",
        90: "5–6 x 800m @ 90% / 2–3 min walk/jog",
        95: "6–8 x 600m @ 95% / 2–3 min walk/jog",
        100: "5 x 600m @ 100% / 3 min walk/jog",
        105: "8–10 x 300m @ 105% / 2 min walk",
        110: "12 x 200m @ 110% / 2 min walk",
        115: "8–10 x 120m @ 115% / 3–5 min walk",
    },
    "mile": {
        80: "6–8 x 1 km @ 80% / 1–2 min jog or 3–5 mi @ 80%",
        85: "5–7 x 1 km @ 85% / 1.5–3 min walk/jog",
        90: "5–6 x 800m @ 90% / 2–3 min walk/jog",
        95: "6–8 x 600m @ 95% / 2–3 min walk/jog",
        100: "5 x 600m @ 100% / 3 min walk/jog",
        105: "8–10 x 300m @ 105% / 2 min walk",
        110: "12 x 200m @ 110% / 2 min walk",
        115: "8–10 x 120m @ 115% / 3–5 min walk",
    },
    "3k": {
        80: "4–8 mi @ 80% or 3–4 sets of (1.5 mi @ 80%, 0.5 mi moderate)",
        85: "6–8 x 1 km @ 85% / 1 min jog or 3.5–6 mi @ 85%",
        90: "4–6 km @ 90% or 3–4 x mile @ 90% / 3 min jog",
        95: "8 x 800m @ 95% / 2 min jog",
        100: "8 x 600m @ 100% / 2–3 min jog",
        105: "6–7 x 500m @ 105% / 2–3 min walk/jog",
        110: "16 x 200m @ 110% / 2 min jog",
        115: "10–12 x 150m @ 115% / 2 min walk",
    },
    "5k": {
        80: "8–15 mi @ 80%",
        85: "5–9 mi @ 85%",
        90: "4–7 mi @ 90%",
        95: "4 x 2 km @ 95% / 3 min jog or 4–6 km continuous @ 95%",
        100: "5–6 x 1200m @ 100% / 3 min jog",
        105: "2 sets of (5–6 x 500m @ 105%) / 45 sec + 4–5 min set break",
        110: "16 x 200m @ 110% / 1–2 min jog",
        115: "10–12 x 200m @ 115% / 2–3 min walk/jog",
    },
    "10k": {
        80: "11–15 mi easy / basic endurance support",
        85: "10–13 mi @ 85%",
        90: "8–10 mi @ 90%",
        95: "5–8 mi @ 95% or 7–8 x (1 km @ 95%, 1 km @ 85%)",
        100: "5 x 2 km @ 100% / 3 min jog",
        105: "2 sets of (1200m, 1000m, 800m, 500m) @ 102–107% / 3 min jog",
        110: "2–3 sets of 4–5 x 500m @ 107–110% with short recovery and set break",
        115: "Short 200–300m fast support with full recovery",
    },
    "half_marathon": {
        80: "10–18 mi at 80–85%",
        85: "10–18 mi at 80–85%",
        90: "10–18 mi @ 90%",
        95: "10–15 mi @ 95%",
        100: "5–6 sets of (3 km @ 100%, 1 km @ 90%)",
        105: "5 x 2 km @ 105% / 3 min jog or 5–6 km @ 105%",
        110: "8 x 800m @ 110% / 2 min jog",
        115: "12 x 300m @ 115% / 100m jog",
    },
    "marathon": {
        80: "15–22 mi at 80–85%",
        85: "15–22 mi at 80–85%",
        90: "15–22 mi @ 90%",
        95: "15–20 mi @ 95%",
        100: "5 sets of (4 km @ 100%, 1 km @ 90%)",
        105: "8–10 sets of (1 km @ 105%, 1 km @ 90%) or 4–5.5 mi @ 105%",
        110: "3 x 3 km @ 110% / 3 min jog",
        115: "8 x 800m @ 115% / 1.5–2 min jog",
    },
}


PROGRESSION_STEPS: Dict[str, Dict[int, List[str]]] = {
    "800m": {
        90: ["3 x 400m @ 90%", "4 x 400m @ 90%", "4 x 500m @ 90%", "4–5 x 500m @ 90%"],
        95: ["3 x 500m @ 95%", "4 x 500m @ 95%", "3 x 600m @ 95%", "3–4 x 600m @ 95%"],
        100: ["3 x 300m @ 100%", "3 x 400m @ 100%", "3 x 450m @ 100%", "3 x 500m @ 100%"],
        105: ["4 x 200m @ 105%", "5 x 200m @ 105%", "5 x 300m @ 105%", "6 x 300m @ 105%"],
        110: ["6 x 150m @ 110%", "8 x 150m @ 110%", "10 x 200m @ 110%", "10–12 x 200m @ 110%"],
    },
    "1500m": {
        90: ["4 x 600m @ 90%", "5 x 600m @ 90%", "5 x 800m @ 90%", "5–6 x 800m @ 90%"],
        95: ["4 x 500m @ 95%", "5 x 500m @ 95%", "6 x 600m @ 95%", "6–8 x 600m @ 95%"],
        100: ["4 x 400m @ 100%", "4 x 500m @ 100%", "5 x 500m @ 100%", "5 x 600m @ 100%"],
        105: ["6 x 200m @ 105%", "8 x 200m @ 105%", "8 x 300m @ 105%", "8–10 x 300m @ 105%"],
        110: ["8 x 150m @ 110%", "10 x 150m @ 110%", "10 x 200m @ 110%", "12 x 200m @ 110%"],
    },
    "mile": {
        90: ["4 x 600m @ 90%", "5 x 600m @ 90%", "5 x 800m @ 90%", "5–6 x 800m @ 90%"],
        95: ["4 x 500m @ 95%", "5 x 500m @ 95%", "6 x 600m @ 95%", "6–8 x 600m @ 95%"],
        100: ["4 x 400m @ 100%", "4 x 500m @ 100%", "5 x 500m @ 100%", "5 x 600m @ 100%"],
        105: ["6 x 200m @ 105%", "8 x 200m @ 105%", "8 x 300m @ 105%", "8–10 x 300m @ 105%"],
        110: ["8 x 150m @ 110%", "10 x 150m @ 110%", "10 x 200m @ 110%", "12 x 200m @ 110%"],
    },
    "3k": {
        90: ["3 x 1 km @ 90%", "4 x 1 km @ 90%", "3 x mile @ 90%", "4–6 km @ 90%"],
        95: ["5 x 800m @ 95%", "6 x 800m @ 95%", "7 x 800m @ 95%", "8 x 800m @ 95%"],
        100: ["5 x 600m @ 100%", "6 x 600m @ 100%", "7 x 600m @ 100%", "8 x 600m @ 100%"],
        105: ["4 x 500m @ 105%", "5 x 500m @ 105%", "6 x 500m @ 105%", "6–7 x 500m @ 105%"],
        110: ["8 x 200m @ 110%", "10 x 200m @ 110%", "12 x 200m @ 110%", "16 x 200m @ 110%"],
    },
    "5k": {
        90: ["4 mi @ 90%", "5 mi @ 90%", "6 mi @ 90%", "4–7 mi @ 90%"],
        95: ["4 km @ 95%", "3 x 2 km @ 95%", "4 x 2 km @ 95%", "4–6 km continuous or 4 x 2 km @ 95%"],
        100: ["4 x 1200m @ 100%", "5 x 1200m @ 100%", "5 x 1200m @ 100% / stronger", "5–6 x 1200m @ 100%"],
        105: [
            "8 x 500m @ 105% in 2 sets",
            "10 x 500m @ 105% in 2 sets",
            "2 sets of 5 x 500m @ 105%",
            "2 sets of 5–6 x 500m @ 105%",
        ],
        110: ["10 x 200m @ 110%", "12 x 200m @ 110%", "14 x 200m @ 110%", "16 x 200m @ 110%"],
    },
    "10k": {
        90: ["5 mi @ 90%", "6–7 mi @ 90%", "8 mi @ 90%", "8–10 mi @ 90%"],
        95: [
            "4 mi @ 95%",
            "5 mi @ 95%",
            "6–7 sets of 1k @ 95% / 1k @ 85%",
            "5–8 mi @ 95% or 7–8 x (1k @ 95%, 1k @ 85%)",
        ],
        100: [
            "8 x 1 km @ 100%",
            "4 x 2 km @ 100%",
            "5 x 2 km @ 100%",
            "3k + 2k + 2k + 1k @ 100–107%",
        ],
        105: [
            "10 x 2 min @ 105%",
            "6 x 1 km @ 105%",
            "2 sets of 6 x 500m @ 105%",
            "2 sets of (1200, 1000, 800, 500) @ 102–107%",
        ],
        110: [
            "5 x 300m @ 110–112%",
            "2 sets of 400-300-200 @ 110–115%",
            "2 sets of 4 x 500m @ 107–110%",
            "2–3 sets of 4–5 x 500m @ 107–110%",
        ],
    },
    "half_marathon": {
        90: ["8 mi @ 90%", "10 mi @ 90%", "12 mi @ 90%", "10–18 mi @ 90%"],
        95: ["8 mi @ 95%", "10 mi @ 95%", "12 mi @ 95%", "10–15 mi @ 95%"],
        100: [
            "3 x (2 km @ 100%, 1 km @ 90%)",
            "4 x (3 km @ 100%, 1 km @ 90%)",
            "5 x (3 km @ 100%, 1 km @ 90%)",
            "5–6 x (3 km @ 100%, 1 km @ 90%)",
        ],
        105: ["3 x 2 km @ 105%", "4 x 2 km @ 105%", "5 x 2 km @ 105%", "5 x 2 km or 5–6 km @ 105%"],
        110: ["4 x 800m @ 110%", "6 x 800m @ 110%", "7 x 800m @ 110%", "8 x 800m @ 110%"],
    },
    "marathon": {
        90: ["10 mi @ 90%", "12–14 mi @ 90%", "15–18 mi @ 90%", "15–22 mi @ 90%"],
        95: ["8–10 mi @ 95%", "12 mi @ 95%", "14–16 mi @ 95%", "15–20 mi @ 95%"],
        100: [
            "3 x (4 km @ 100%, 1 km @ 90%)",
            "4 x (4 km @ 100%, 1 km @ 90%)",
            "5 x (4 km @ 100%, 1 km @ 90%)",
            "5 sets of (4 km @ 100%, 1 km @ 90%)",
        ],
        105: [
            "4 x (1 km @ 105%, 1 km @ 90%)",
            "6 x (1 km @ 105%, 1 km @ 90%)",
            "8 x (1 km @ 105%, 1 km @ 90%)",
            "8–10 x (1 km @ 105%, 1 km @ 90%)",
        ],
        110: ["2 x 2 km @ 110%", "2 x 3 km @ 110%", "3 x 3 km @ 110%", "3 x 3 km @ 110%"],
    },
}


GENERAL_PHASE_OPTIONS: Dict[str, List[str]] = {
    "middle_distance": [
        "10 x 1 min @ 105% / 1 min easy",
        "8 x 90 sec @ 105–110% / full jog",
        "12 x 30 sec @ 110–115% / easy jog",
    ],
    "distance": [
        "8 x 2 min @ 105% / 90 sec easy",
        "3 sets of 3-2-1 min @ 100–108% / equal easy jog",
        "20–30 min Kenyan-style progression finishing around 90% effort",
    ],
    "long_distance": [
        "5 mi steady @ 80–85%",
        "3 x 10 min @ 90% / 3 min easy",
        "8 x 2 min @ 105% / 90 sec easy",
    ],
    "marathon": [
        "6–8 mi steady @ 80–85%",
        "3 x 10 min @ 90% / 3 min easy",
        "8 x 2 min @ 105% / 90 sec easy",
    ],
}


def get_final_targets_for_event(race_distance: str) -> Dict[int, str]:
    return FINAL_TARGETS[race_distance]


def _event_category(race_distance: str) -> str:
    if race_distance in {"800m", "1500m", "mile"}:
        return "middle_distance"
    if race_distance in {"3k", "5k", "10k"}:
        return "distance"
    if race_distance == "half_marathon":
        return "long_distance"
    return "marathon"


def get_progression_session(
    race_distance: str,
    band: int,
    phase_progress: float,
) -> str:
    """
    phase_progress should be 0.0 -> 1.0 within that phase.
    """
    options = PROGRESSION_STEPS.get(race_distance, {}).get(band)
    if not options:
        return FINAL_TARGETS[race_distance].get(band, f"Work at {band}%")

    idx = min(len(options) - 1, max(0, int(round(phase_progress * (len(options) - 1)))))
    return options[idx]


def get_general_session(
    race_distance: str,
    phase_week: int,
) -> str:
    category = _event_category(race_distance)
    options = GENERAL_PHASE_OPTIONS[category]
    return options[(phase_week - 1) % len(options)]


def get_long_run_description(
    race_distance: str,
    long_run_miles: int,
    phase: str,
) -> str:
    category = _event_category(race_distance)

    if category == "middle_distance":
        return f"{long_run_miles} mi easy with 6 x 20 sec relaxed fast strides"

    if phase == "general":
        return f"{long_run_miles} mi easy, optionally finishing moderate"
    if phase == "supportive":
        return f"{long_run_miles} mi with last 20–30 min steady to strong"
    return f"{max(long_run_miles - 1, 6)} to {long_run_miles} mi mostly easy, keep fresh for workouts"


def easy_run_description(miles: int, include_strides: bool = False) -> str:
    session = f"{miles} mi easy"
    if include_strides:
        session += " + 4–6 x 20 sec strides"
    return session
