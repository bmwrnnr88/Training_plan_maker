from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd

from config import PEAK_EQUIVALENTS_5K
from models import PercentWorkout
from workouts_5k import WORKOUT_DB_5K

METERS_PER_MILE = 1609.344


def format_percent(percent: int) -> str:
    """Format a percent rung for display."""
    return f"{percent}%"


def format_secondary_percents(percents: Iterable[int]) -> str:
    """Format optional secondary percent rungs for display."""
    values = list(percents)
    if not values:
        return "None"
    return ", ".join(format_percent(percent) for percent in values)


def sort_workouts(workouts: Iterable[PercentWorkout]) -> List[PercentWorkout]:
    """Sort workout templates from simpler to denser progressions."""
    return sorted(
        workouts,
        key=lambda workout: (
            workout.progression_order,
            workout.difficulty_rank,
            workout.equivalent_volume_m,
        ),
    )


def meters_to_miles(distance_m: float) -> float:
    """Convert meters to miles."""
    return distance_m / METERS_PER_MILE


def miles_to_meters(distance_miles: float) -> int:
    """Convert miles to rounded meters."""
    return int(round(distance_miles * METERS_PER_MILE))


def format_equivalent_volume(distance_m: int) -> str:
    """Format equivalent volume in both miles and meters."""
    return f"{meters_to_miles(distance_m):.2f} mi ({distance_m:,} m)"


def workout_style_label(workout: PercentWorkout) -> str:
    """Collapse workout templates into readable reference styles."""
    if workout.build_direction == "maintenance":
        return "Maintenance"
    if workout.family == "single_percent_continuous":
        return "Continuous"
    if workout.family == "single_percent_intervals":
        return "Intervals"
    if workout.build_direction == "bottom_up":
        return "Bottom-up intervals"
    if workout.build_direction == "top_down":
        return "Top-down blend"
    if workout.build_direction == "alternation":
        return "Alternation"
    if workout.build_direction in {"blend", "combo"}:
        return "Blend"
    return workout.build_direction.replace("_", " ").title()


def peak_workout_references(percent: int) -> List[dict]:
    """Return representative peak workout references for a rung by style."""
    candidates = [
        workout for workout in WORKOUT_DB_5K if workout.primary_percent == percent
    ]
    best_by_style: Dict[str, PercentWorkout] = {}

    for workout in candidates:
        style = workout_style_label(workout)
        current_best = best_by_style.get(style)
        if current_best is None or workout.equivalent_volume_m > current_best.equivalent_volume_m:
            best_by_style[style] = workout

    references = [
        {
            "style": style,
            "workout_text": workout.workout_text,
            "equivalent_volume_m": workout.equivalent_volume_m,
        }
        for style, workout in sorted(
            best_by_style.items(),
            key=lambda item: item[1].equivalent_volume_m,
            reverse=True,
        )
    ]
    return references


def capacity_table(completed_equivalents_m: Dict[int, int], capacities: Dict[int, float]) -> pd.DataFrame:
    """Render capacities into a readable completed-vs-peak table."""
    rows = [
        {
            "Percent": format_percent(percent),
            "Completed": f"{meters_to_miles(completed_equivalents_m[percent]):.2f} mi",
            "Peak": f"{meters_to_miles(PEAK_EQUIVALENTS_5K[percent]):.2f} mi",
            "Build": round(capacities[percent], 2),
        }
        for percent in sorted(capacities)
    ]
    return pd.DataFrame(rows)
