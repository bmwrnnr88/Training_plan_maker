from __future__ import annotations

from typing import Dict

FINAL_TARGETS = {
    "800m": {
        90: "3 x 600m @ 90%",
        95: "4 x 500m @ 95%",
        100: "5 x 300m @ 100%",
        105: "4 x 200m @ 105%",
        110: "6 x 150m @ 110%",
    },
    "1500m": {
        90: "4 x 800m @ 90%",
        95: "5 x 600m @ 95%",
        100: "5 x 400m @ 100%",
        105: "6 x 300m @ 105%",
        110: "8 x 200m @ 110%",
    },
    "mile": {
        90: "4 x 800m @ 90%",
        95: "5 x 600m @ 95%",
        100: "5 x 400m @ 100%",
        105: "6 x 300m @ 105%",
        110: "8 x 200m @ 110%",
    },
    "3k": {
        90: "4 mi continuous @ 90%",
        95: "4 x 1k @ 95%",
        100: "5 x 1k @ 100%",
        105: "6 x 600m @ 105%",
        110: "8 x 300m @ 110%",
    },
    "5k": {
        90: "7 mi continuous @ 90%",
        95: "6 mi continuous @ 95%",
        100: "4 x 1600m @ 100%",
        105: "6 x 1k @ 105%",
        110: "2 sets of 5 x 400m @ 110%",
    },
    "10k": {
        90: "10 mi continuous @ 90%",
        95: "7–8 mi continuous @ 95%",
        100: "5 x 2k @ 100%",
        105: "6 x 1k @ 105%",
        110: "3 sets of 500m reps @ 110%",
    },
    "half_marathon": {
        90: "12 mi continuous @ 90%",
        95: "10–15 mi continuous @ 95%",
        100: "6–8 mi at race effort",
        105: "6 km @ 105%",
        110: "8 x 800m @ 110%",
    },
    "marathon": {
        90: "15–22 mi @ 90%",
        95: "15–20 mi @ 95%",
        100: "alternating 1k on / 1k steady near race effort",
        105: "short controlled reps @ 105%",
        110: "very limited fast support",
    },
}


def easy_run_description(miles: int, include_strides: bool = False) -> str:
    session = f"{miles} mi easy"
    if include_strides:
        session += " + 4–6 x 20 sec strides"
    return session


def long_run_description(
    race_distance: str,
    event_category: str,
    paces: dict,
    long_run_miles: int,
    phase: str,
) -> str:
    def pace(band: int) -> str:
        return paces[band]["pace_per_mile"]

    if event_category == "middle_distance":
        return f"{long_run_miles} mi easy with 6 x 20 sec relaxed fast strides"

    if race_distance == "marathon":
        if phase == "general":
            return f"{long_run_miles} mi easy"
        if phase == "supportive":
            return f"{long_run_miles} mi with last 25–40 min around 90% ({pace(90)}/mi)"
        return f"{max(long_run_miles - 2, 8)}–{long_run_miles} mi mostly easy, stay fresh for key workouts"

    if race_distance == "half_marathon":
        if phase == "general":
            return f"{long_run_miles} mi easy, optionally finishing moderate"
        if phase == "supportive":
            return f"{long_run_miles} mi with last 20–30 min around 90% ({pace(90)}/mi)"
        return f"{max(long_run_miles - 1, 8)}–{long_run_miles} mi mostly easy, keep the quality for workout days"

    if phase == "general":
        return f"{long_run_miles} mi easy, optionally finishing moderate"
    if phase == "supportive":
        return f"{long_run_miles} mi with last 15–25 min around 85% ({pace(85)}/mi)"
    return f"{max(long_run_miles - 1, 7)}–{long_run_miles} mi mostly easy, keep fresh for race-specific sessions"


def general_filler_workout(
    race_distance: str,
    event_category: str,
    paces: Dict[int, Dict[str, str]],
    phase_week: int,
    phase_total: int,
) -> str:
    if event_category == "middle_distance":
        options = [
            "10 x 1 min fast / 1 min easy",
            "8 x 90 sec @ 105–110% / full jog",
            "12 x 30 sec @ 110–115% / easy jog",
        ]
    elif race_distance in {"half_marathon", "marathon"}:
        options = [
            "6 mi steady",
            f"3 x 10 min @ 90% ({paces[90]['pace_per_mile']}/mi) / 3 min easy",
            f"8 x 2 min @ 105% ({paces[105]['pace_per_mile']}/mi) / 90 sec easy",
        ]
    else:
        options = [
            f"8 x 2 min @ 105% ({paces[105]['pace_per_mile']}/mi) / 90 sec easy",
            "3 sets of 3-2-1 min from 100% to 108% / equal jog",
            "20–30 min progression finishing around 90% effort",
        ]

    return options[(phase_week - 1) % len(options)]


def build_progression_session(
    race_distance: str,
    band: int,
    paces: Dict[int, Dict[str, str]],
    step_index: int,
    total_steps: int,
    athlete_mileage: int,
) -> str:
    band_pace_mi = paces[band]["pace_per_mile"]
    band_pace_km = paces[band]["pace_per_km"]
    progress = step_index / max(1, total_steps)

    if race_distance == "10k":
        if band == 90:
            miles = round(5 + 5 * progress)
            return f"{miles} mi continuous @ 90% ({band_pace_mi}/mi)"
        if band == 95:
            miles = round(4 + 4 * progress)
            return f"{miles} mi continuous @ 95% ({band_pace_mi}/mi)"
        if band == 100:
            reps = min(5, max(3, round(3 + 2 * progress)))
            return f"{reps} x 2k @ 100% ({band_pace_km}/km) / 3 min jog"
        if band == 105:
            reps = min(6, max(4, round(4 + 2 * progress)))
            return f"{reps} x 1k @ 105% ({band_pace_km}/km) / 2 min jog"
        if band == 110:
            reps = min(15, max(8, round(8 + 7 * progress)))
            return f"{reps} x 300m @ 110% effort / walk-jog recovery"

    if race_distance == "5k":
        if band == 90:
            miles = round(4 + 4 * progress)
            return f"{miles} mi continuous @ 90% ({band_pace_mi}/mi)"
        if band == 95:
            miles = round(3 + 3 * progress)
            return f"{miles} mi continuous @ 95% ({band_pace_mi}/mi)"
        if band == 100:
            reps = min(5, max(3, round(3 + 2 * progress)))
            return f"{reps} x 1600m @ 100% / 3 min jog"
        if band == 105:
            reps = min(6, max(4, round(4 + 2 * progress)))
            return f"{reps} x 1k @ 105% ({band_pace_km}/km) / 2 min jog"
        if band == 110:
            reps = min(10, max(6, round(6 + 4 * progress)))
            return f"{reps} x 400m @ 110% / 200m jog"

    if race_distance == "half_marathon":
        if band == 90:
            miles = round(7 + 5 * progress)
            return f"{miles} mi continuous @ 90% ({band_pace_mi}/mi)"
        if band == 95:
            miles = round(6 + 6 * progress)
            return f"{miles} mi continuous @ 95% ({band_pace_mi}/mi)"
        if band == 100:
            miles = round(4 + 4 * progress)
            return f"{miles} mi at race effort"
        if band == 105:
            km = round(3 + 3 * progress)
            return f"{km} km continuous @ 105% ({band_pace_km}/km)"
        if band == 110:
            reps = min(8, max(4, round(4 + 4 * progress)))
            return f"{reps} x 800m @ 110% / 2 min jog"

    if race_distance == "marathon":
        if band == 90:
            miles = round(10 + 10 * progress)
            return f"{miles} mi continuous @ 90% ({band_pace_mi}/mi)"
        if band == 95:
            miles = round(8 + 8 * progress)
            return f"{miles} mi continuous @ 95% ({band_pace_mi}/mi)"
        if band == 100:
            km = round(6 + 8 * progress)
            return f"{km} x 1k alternating race effort / steady"
        if band == 105:
            reps = min(8, max(4, round(4 + 4 * progress)))
            return f"{reps} x 2 min @ 105% / 2 min easy"
        if band == 110:
            return "6 x 30 sec fast relaxed running / full recovery"

    if band == 90:
        return f"30–40 min continuous @ 90% ({band_pace_mi}/mi)"
    if band == 95:
        return f"4–6 x 1k @ 95% ({band_pace_km}/km) / 2 min jog"
    if band == 100:
        return f"5 x 800m @ 100% ({band_pace_km}/km) / 2–3 min jog"
    if band == 105:
        return "6 x 400m @ 105% / full jog"
    if band == 110:
        return "8 x 200m @ 110% / full recovery"

    return f"Short fast relaxed reps around {band}% effort"
