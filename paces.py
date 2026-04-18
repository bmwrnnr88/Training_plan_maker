---

## `paces.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


SUPPORTED_DISTANCES_M = {
    "800m": 800.0,
    "1500m": 1500.0,
    "mile": 1609.344,
    "3000m": 3000.0,
    "5k": 5000.0,
    "10k": 10000.0,
    "half marathon": 21097.5,
    "marathon": 42195.0,
}


PACE_BANDS = [80, 85, 90, 95, 100, 105, 110, 115]


@dataclass
class PaceBand:
    percent: int
    seconds_per_km: float
    seconds_per_mile: float
    label: str


def parse_time_to_seconds(time_str: str) -> int:
    """
    Accepts 'MM:SS' or 'H:MM:SS'.
    """
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + int(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    raise ValueError("Time must look like MM:SS or H:MM:SS")


def format_seconds_to_clock(total_seconds: float) -> str:
    total_seconds = int(round(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_pace(seconds: float) -> str:
    minutes = int(seconds // 60)
    sec = int(round(seconds % 60))
    if sec == 60:
        minutes += 1
        sec = 0
    return f"{minutes}:{sec:02d}"


def race_time_to_base_pace(distance_name: str, race_time_str: str) -> Dict[str, float]:
    if distance_name not in SUPPORTED_DISTANCES_M:
        raise ValueError(f"Unsupported distance: {distance_name}")

    total_seconds = parse_time_to_seconds(race_time_str)
    meters = SUPPORTED_DISTANCES_M[distance_name]

    seconds_per_meter = total_seconds / meters
    seconds_per_km = seconds_per_meter * 1000.0
    seconds_per_mile = seconds_per_meter * 1609.344

    return {
        "race_time_seconds": total_seconds,
        "distance_m": meters,
        "seconds_per_meter": seconds_per_meter,
        "seconds_per_km": seconds_per_km,
        "seconds_per_mile": seconds_per_mile,
    }


def build_percentage_paces(distance_name: str, race_time_str: str) -> Dict[int, PaceBand]:
    """
    In this framework, 100% = current race pace.
    Faster percentages have lower seconds-per-distance.
    Example: 105% pace means moving 5% faster than race pace.
    """
    base = race_time_to_base_pace(distance_name, race_time_str)
    base_km = base["seconds_per_km"]
    base_mile = base["seconds_per_mile"]

    labels = {
        80: "general endurance floor",
        85: "steady / supportive endurance bridge",
        90: "race-supportive endurance",
        95: "race-specific endurance",
        100: "race pace",
        105: "race-specific speed",
        110: "race-supportive speed",
        115: "mechanical / fast support",
    }

    paces: Dict[int, PaceBand] = {}
    for pct in PACE_BANDS:
        factor = 100.0 / pct
        paces[pct] = PaceBand(
            percent=pct,
            seconds_per_km=base_km * factor,
            seconds_per_mile=base_mile * factor,
            label=labels[pct],
        )
    return paces


def pace_table_for_display(distance_name: str, race_time_str: str) -> Dict[str, Dict[str, str]]:
    bands = build_percentage_paces(distance_name, race_time_str)
    output: Dict[str, Dict[str, str]] = {}
    for pct, band in bands.items():
        output[f"{pct}%"] = {
            "label": band.label,
            "per_km": format_pace(band.seconds_per_km),
            "per_mile": format_pace(band.seconds_per_mile),
        }
    return output


def convert_distance_for_repetition(distance_name: str) -> Tuple[str, str]:
    """
    Convenience helper for workout display.
    """
    if distance_name in {"800m", "1500m", "mile", "3000m"}:
        return ("track", "meters")
    return ("road", "mixed")
