from __future__ import annotations

from typing import Dict

from workout_evolution_system.utils import MILES_IN_5K, pace_to_string, parse_time_to_seconds


PACE_BANDS = [80, 85, 90, 95, 100, 105, 110, 115]

ZONE_BY_BAND = {
    80: "easy",
    85: "steady",
    90: "supportive_endurance",
    95: "threshold",
    100: "race",
    105: "cv",
    110: "speed",
    115: "speed",
}


def build_fixed_pace_ladder(athlete_profile: Dict[str, str]) -> Dict[int, Dict[str, float | str]]:
    if "5k" not in athlete_profile:
        raise ValueError("athlete_profile must include a 5k mark.")

    five_k_seconds = parse_time_to_seconds(athlete_profile["5k"])
    five_k_seconds_per_mile = five_k_seconds / MILES_IN_5K
    five_k_seconds_per_km = five_k_seconds / 5.0

    ladder: Dict[int, Dict[str, float | str]] = {}

    for band in PACE_BANDS:
        fraction = band / 100.0
        seconds_per_mile = five_k_seconds_per_mile / fraction
        seconds_per_km = five_k_seconds_per_km / fraction

        ladder[band] = {
            "band": band,
            "zone": ZONE_BY_BAND[band],
            "seconds_per_mile": seconds_per_mile,
            "seconds_per_km": seconds_per_km,
            "pace_per_mile": pace_to_string(seconds_per_mile),
            "pace_per_km": pace_to_string(seconds_per_km),
        }

    return ladder
