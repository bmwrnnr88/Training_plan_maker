from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

PACE_BANDS = [80, 85, 90, 95, 100, 105, 110, 115]
FIVE_K_DISTANCE_KM = 5.0
KM_PER_MILE = 1.60934


@dataclass(frozen=True)
class PaceInfo:
    """Pace information anchored to current 5K fitness."""

    time_seconds: float
    seconds_per_km: float
    seconds_per_mile: float


def parse_time_to_seconds(time_str: str) -> int:
    """Parse a clock string in mm:ss or hh:mm:ss format."""
    parts = time_str.strip().split(":")

    if len(parts) not in {2, 3}:
        raise ValueError("Time must be in mm:ss or hh:mm:ss format.")
    if not all(part.isdigit() for part in parts):
        raise ValueError("Time must contain only numbers separated by colons.")

    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        if seconds >= 60:
            raise ValueError("Seconds must be between 00 and 59.")
        total_seconds = minutes * 60 + seconds
    else:
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60 or seconds >= 60:
            raise ValueError("In hh:mm:ss format, minutes and seconds must be between 00 and 59.")
        total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds <= 0:
        raise ValueError("Time must be greater than 0 seconds.")

    return total_seconds


def pace_to_string(seconds_per_unit: float) -> str:
    """Format pace as m:ss."""
    minutes = int(seconds_per_unit // 60)
    seconds = int(round(seconds_per_unit % 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def current_5k_pace_info(current_time_str: str) -> PaceInfo:
    """Build pace info from a current 5K mark."""
    time_seconds = parse_time_to_seconds(current_time_str)
    seconds_per_km = time_seconds / FIVE_K_DISTANCE_KM
    seconds_per_mile = seconds_per_km * KM_PER_MILE
    return PaceInfo(
        time_seconds=time_seconds,
        seconds_per_km=seconds_per_km,
        seconds_per_mile=seconds_per_mile,
    )


def get_percentage_paces(current_time_str: str) -> Dict[int, Dict[str, float | str]]:
    """Return the full fixed pace ladder from current 5K fitness."""
    pace_info = current_5k_pace_info(current_time_str)
    paces: Dict[int, Dict[str, float | str]] = {}

    for percent in PACE_BANDS:
        fraction = percent / 100.0
        seconds_per_km = pace_info.seconds_per_km / fraction
        seconds_per_mile = pace_info.seconds_per_mile / fraction
        paces[percent] = {
            "seconds_per_km": seconds_per_km,
            "seconds_per_mile": seconds_per_mile,
            "pace_per_km": pace_to_string(seconds_per_km),
            "pace_per_mile": pace_to_string(seconds_per_mile),
        }

    return paces
