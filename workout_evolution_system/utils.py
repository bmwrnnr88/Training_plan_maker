from __future__ import annotations

from math import isnan
from typing import Any


METERS_PER_MILE = 1609.344
MILES_IN_5K = 5000 / METERS_PER_MILE


def parse_time_to_seconds(time_str: str) -> int:
    parts = time_str.strip().split(":")

    if len(parts) not in {2, 3}:
        raise ValueError("Time must be in mm:ss or hh:mm:ss format.")

    if not all(part.isdigit() for part in parts):
        raise ValueError("Time must contain only digits separated by colons.")

    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        if seconds >= 60:
            raise ValueError("Seconds must be between 00 and 59.")
        total_seconds = minutes * 60 + seconds
    else:
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Minutes and seconds must be between 00 and 59.")
        total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds <= 0:
        raise ValueError("Time must be greater than zero.")

    return total_seconds


def seconds_to_clock(total_seconds: float) -> str:
    whole_seconds = int(round(total_seconds))
    minutes = whole_seconds // 60
    seconds = whole_seconds % 60
    return f"{minutes}:{seconds:02d}"


def pace_to_string(seconds_per_unit: float) -> str:
    minutes = int(seconds_per_unit // 60)
    seconds = int(round(seconds_per_unit % 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def miles_to_meters(distance_miles: float) -> int:
    return int(round(distance_miles * METERS_PER_MILE))


def meters_to_miles(distance_meters: float) -> float:
    return float(distance_meters) / METERS_PER_MILE


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def round_to_half_mile(value: float) -> float:
    return round(value * 2) / 2


def clean_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default

    if isinstance(value, float) and isnan(value):
        return default

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        return float(stripped)

    return float(value)
