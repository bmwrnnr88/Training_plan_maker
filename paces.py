from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


DISTANCE_KM = {
    "800m": 0.8,
    "1500m": 1.5,
    "mile": 1.60934,
    "3k": 3.0,
    "5k": 5.0,
    "10k": 10.0,
    "half_marathon": 21.0975,
    "marathon": 42.195,
}

PACE_BANDS = [80, 85, 90, 95, 100, 105, 110, 115]


@dataclass
class PaceInfo:
    distance: str
    time_seconds: float
    seconds_per_km: float
    seconds_per_mile: float


def parse_time_to_seconds(time_str: str) -> int:
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


def seconds_to_clock(total_seconds: float) -> str:
    total_seconds = int(round(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def pace_to_string(seconds_per_unit: float) -> str:
    minutes = int(seconds_per_unit // 60)
    seconds = int(round(seconds_per_unit % 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def race_time_to_pace_info(distance: str, time_str: str) -> PaceInfo:
    if distance not in DISTANCE_KM:
        raise ValueError(f"Unsupported distance: {distance}")

    time_seconds = parse_time_to_seconds(time_str)
    km = DISTANCE_KM[distance]
    sec_per_km = time_seconds / km
    sec_per_mile = sec_per_km * 1.60934

    return PaceInfo(
        distance=distance,
        time_seconds=time_seconds,
        seconds_per_km=sec_per_km,
        seconds_per_mile=sec_per_mile,
    )


def equivalent_time(target_distance: str, source_distance: str, source_time_seconds: float) -> float:
    if source_distance == target_distance:
        return source_time_seconds

    d1 = DISTANCE_KM[source_distance]
    d2 = DISTANCE_KM[target_distance]
    exponent = 1.06
    return source_time_seconds * (d2 / d1) ** exponent


def get_target_pace_info(
    target_distance: str,
    current_distance: str,
    current_time_str: str,
) -> PaceInfo:
    source = race_time_to_pace_info(current_distance, current_time_str)
    target_time = equivalent_time(target_distance, current_distance, source.time_seconds)
    sec_per_km = target_time / DISTANCE_KM[target_distance]
    sec_per_mile = sec_per_km * 1.60934

    return PaceInfo(
        distance=target_distance,
        time_seconds=target_time,
        seconds_per_km=sec_per_km,
        seconds_per_mile=sec_per_mile,
    )


def get_percentage_paces(target_pace_info: PaceInfo) -> Dict[int, Dict[str, float | str]]:
    paces: Dict[int, Dict[str, float | str]] = {}

    for pct in PACE_BANDS:
        frac = pct / 100.0
        sec_per_km = target_pace_info.seconds_per_km / frac
        sec_per_mile = target_pace_info.seconds_per_mile / frac

        paces[pct] = {
            "seconds_per_km": sec_per_km,
            "seconds_per_mile": sec_per_mile,
            "pace_per_km": pace_to_string(sec_per_km),
            "pace_per_mile": pace_to_string(sec_per_mile),
        }

    return paces
