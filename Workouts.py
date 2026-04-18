from __future__ import annotations

from typing import Dict, List


def _band_pace(paces: Dict[int, Dict[str, str]], pct: int) -> str:
    return paces[pct]["pace_per_mile"]


def general_workout(event_category: str, paces: Dict[int, Dict[str, str]], week_in_phase: int) -> str:
    if event_category == "middle_distance":
        options = [
            f"10 x 1 min @ 105% ({_band_pace(paces, 105)}/mi effort) / 1 min easy",
            f"8 x 90 sec @ 105–110% ({_band_pace(paces, 105)}–{_band_pace(paces, 110)}/mi effort) / full jog",
            f"12 x 30 sec fast @ 110–115% ({_band_pace(paces, 110)}–{_band_pace(paces, 115)}/mi effort) / easy jog",
        ]
    elif event_category == "marathon":
        options = [
            f"6 mi steady @ 85% ({_band_pace(paces, 85)}/mi)",
            f"3 x 10 min @ 90% ({_band_pace(paces, 90)}/mi) / 3 min easy",
            f"8 x 2 min @ 105% ({_band_pace(paces, 105)}/mi) / 90 sec easy",
        ]
    else:
        options = [
            f"8 x 2 min @ 105% ({_band_pace(paces, 105)}/mi) / 90 sec easy",
            f"3 sets of 3-2-1 min @ 100–108% ({_band_pace(paces, 100)} to {_band_pace(paces, 110)}/mi) / equal easy jog",
            f"20–30 min Kenyan-style progression finishing around 90% ({_band_pace(paces, 90)}/mi effort)",
        ]

    return options[(week_in_phase - 1) % len(options)]


def supportive_endurance_workout(
    event_category: str,
    paces: Dict[int, Dict[str, str]],
    week_in_phase: int,
) -> str:
    if event_category == "middle_distance":
        options = [
            f"20 min continuous @ 90% ({_band_pace(paces, 90)}/mi)",
            f"4 x 5 min @ 95% ({_band_pace(paces, 95)}/mi) / 90 sec jog",
            f"5 x 1 km @ 95% ({paces[95]['pace_per_km']}/km) / 2 min jog",
        ]
    elif event_category == "marathon":
        options = [
            f"8–10 mi continuous @ 90% ({_band_pace(paces, 90)}/mi)",
            f"3 x 3 mi @ 95% ({_band_pace(paces, 95)}/mi) / 5 min easy",
            f"10–12 mi progression from 85% to 95% ({_band_pace(paces, 85)} to {_band_pace(paces, 95)}/mi)",
        ]
    else:
        options = [
            f"4–6 mi continuous @ 95% ({_band_pace(paces, 95)}/mi)",
            f"6 x 1 km @ 95% ({paces[95]['pace_per_km']}/km) / 1 km float @ 85% ({paces[85]['pace_per_km']}/km)",
            f"7–9 mi continuous @ 90% ({_band_pace(paces, 90)}/mi)",
        ]

    return options[(week_in_phase - 1) % len(options)]


def supportive_speed_workout(
    event_category: str,
    paces: Dict[int, Dict[str, str]],
    week_in_phase: int,
) -> str:
    if event_category == "middle_distance":
        options = [
            f"2 sets of 5 x 300m @ 110% ({paces[110]['pace_per_km']}/km effort) / 100m walk, 4 min set break",
            f"8 x 200m @ 115% ({paces[115]['pace_per_km']}/km effort) / full recovery",
            f"6 x 400m @ 105–110% / 2 min jog",
        ]
    elif event_category == "marathon":
        options = [
            f"8 x 1 min @ 105% ({_band_pace(paces, 105)}/mi) / 90 sec easy",
            f"10 x 30 sec @ 110% ({_band_pace(paces, 110)}/mi) / full easy jog",
            f"6 x 2 min @ 105% ({_band_pace(paces, 105)}/mi) / 2 min easy",
        ]
    else:
        options = [
            f"2 sets of 6 x 500m @ 105% ({paces[105]['pace_per_km']}/km) / 45–60 sec jog, 4 min set break",
            f"5 x 300m @ 110–112% ({paces[110]['pace_per_km']}/km effort) / 2–3 min walk",
            f"2 sets of 400m-300m-200m @ 110–115% / full walk recovery",
        ]

    return options[(week_in_phase - 1) % len(options)]


def race_specific_workout(
    race_distance: str,
    event_category: str,
    paces: Dict[int, Dict[str, str]],
    week_in_phase: int,
    total_specific_weeks: int,
) -> str:
    if race_distance == "10k":
        progression = [
            f"8 x 1 km @ 100% ({paces[100]['pace_per_km']}/km) / 2 min jog",
            f"4 sets of 1200m @ 100% + 800m @ 103–105% / 1 min walk, 4 min between sets",
            f"4 x 2 km @ 100% ({paces[100]['pace_per_km']}/km) / 3 min jog",
            f"5 x 2 km @ 100% ({paces[100]['pace_per_km']}/km) / 3 min jog",
            f"3k + 2k + 2k + 1k at 100/101/102/105–107%",
        ]
        idx = min(week_in_phase - 1, len(progression) - 1)
        return progression[idx]

    if race_distance == "5k":
        progression = [
            f"6 x 1 km @ 100% ({paces[100]['pace_per_km']}/km) / 2 min jog",
            f"5 x 1200m @ 100% ({paces[100]['pace_per_km']}/km) / 2–3 min jog",
            f"4 x 1600m @ 98–100% / 3 min jog",
            f"3 sets of 1 km @ 100% + 500m @ 105%",
            f"2k + 1600 + 1200 + 800 @ 100–105%",
        ]
        return progression[min(week_in_phase - 1, len(progression) - 1)]

    if race_distance in {"half_marathon", "marathon"}:
        progression = [
            f"3 x 3 mi @ 95% ({_band_pace(paces, 95)}/mi) / 5 min easy",
            f"8–10 mi continuous @ 95% ({_band_pace(paces, 95)}/mi)",
            f"2 x 5 mi @ 95% ({_band_pace(paces, 95)}/mi) / 8 min easy",
            f"12–14 mi progression, finishing around 100% effort segment",
            f"6–8 mi continuous @ 100% race effort",
        ]
        return progression[min(week_in_phase - 1, len(progression) - 1)]

    progression = [
        f"5 x 800m @ 100% ({paces[100]['pace_per_km']}/km) / 2–3 min jog",
        f"4 x 1 km @ 100% ({paces[100]['pace_per_km']}/km) / 3 min jog",
        f"3 x 1200m @ 100% / 3–4 min jog",
        f"Mixed session at 100–105%",
    ]
    return progression[min(week_in_phase - 1, len(progression) - 1)]


def long_run_description(
    event_category: str,
    paces: Dict[int, Dict[str, str]],
    long_run_miles: int,
    phase: str,
) -> str:
    if event_category == "middle_distance":
        return f"{long_run_miles} mi easy with 6 x 20 sec relaxed fast strides"

    if phase == "general":
        return f"{long_run_miles} mi easy, optionally finishing moderate"
    if phase == "supportive":
        return f"{long_run_miles} mi with last 20–30 min around 85% ({_band_pace(paces, 85)}/mi)"
    return f"{long_run_miles - 1} to {long_run_miles} mi mostly easy, keep fresh for workouts"


def easy_run_description(miles: int, include_strides: bool = False) -> str:
    session = f"{miles} mi easy"
    if include_strides:
        session += " + 4–6 x 20 sec strides"
    return session
