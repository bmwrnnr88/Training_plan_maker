from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Tuple

import pandas as pd

from paces import get_percentage_paces, get_target_pace_info, seconds_to_clock
from rules import (
    DAY_ORDER,
    EVENT_CATEGORY,
    PHASE_NAMES,
    choose_phase_lengths,
    hard_day_spacing,
    phase_notes,
    weekly_mileage_targets,
)
from workouts import (
    easy_run_description,
    get_final_targets_for_event,
    get_general_session,
    get_long_run_description,
    get_progression_session,
)


@dataclass
class AthleteProfile:
    current_distance: str
    current_time: str
    current_mileage: int
    max_mileage: int
    days_per_week: int
    long_run_max: int
    day_off: str
    runner_type: str
    experience: str
    doubles: bool
    track_access: bool
    treadmill_access: bool


@dataclass
class GoalProfile:
    race_distance: str
    weeks_to_race: int


def _pace_table_df(paces: Dict[int, Dict[str, str]]) -> pd.DataFrame:
    rows = []
    for pct, data in paces.items():
        rows.append(
            {
                "Percent of race pace": f"{pct}%",
                "Pace / mile": data["pace_per_mile"],
                "Pace / km": data["pace_per_km"],
            }
        )
    return pd.DataFrame(rows)


def _week_in_phase(phases: List[str], idx: int) -> int:
    phase = phases[idx]
    count = 0
    for i in range(idx + 1):
        if phases[i] == phase:
            count += 1
    return count


def _phase_count(phases: List[str], phase_name: str) -> int:
    return phases.count(phase_name)


def _phase_progress(phase_week: int, total_phase_weeks: int) -> float:
    if total_phase_weeks <= 1:
        return 1.0
    return (phase_week - 1) / (total_phase_weeks - 1)


def _band_emphasis_for_phase(race_distance: str, phase: str) -> Tuple[int, int]:
    """
    Picks the week's primary and secondary quality bands based on phase.
    This follows the source logic:
    - general = lower-key general plus endurance support
    - supportive = 90/95/105/110 emphasis
    - specific = 95/100/105 emphasis
    """
    category = EVENT_CATEGORY[race_distance]

    if phase == "general":
        if category == "middle_distance":
            return 105, 90
        return 105, 90

    if phase == "supportive":
        if category == "middle_distance":
            return 95, 110
        if category in {"long_distance", "marathon"}:
            return 95, 105
        return 95, 110

    # specific
    if category == "middle_distance":
        return 100, 95
    if category in {"long_distance", "marathon"}:
        return 100, 95
    return 100, 95


def _event_notes(race_distance: str) -> List[str]:
    if race_distance == "5k":
        return [
            "5k progression emphasizes long fast work at 80%, strong running at 90%, long repeats or continuous running at 95%, and classic race-pace / faster sessions later.",
        ]
    if race_distance == "10k":
        return [
            "10k progression is built around the detailed 10k article’s order: specific work first in concept, then 95/90 endurance support, then 105/110 speed support, then mileage around it.",
        ]
    if race_distance == "half_marathon":
        return [
            "Half marathon progression leans heavily on long work at 90–95%, with 105% and 110% used more sparingly.",
        ]
    if race_distance == "marathon":
        return [
            "Marathon progression leans most heavily on long work at 90–95%, with faster work mostly in supportive doses.",
        ]
    return [
        "This event uses the appendix’s recommended workouts as culminating targets and builds backward toward them.",
    ]


def _build_quality_sessions_for_week(
    race_distance: str,
    phase: str,
    phase_week: int,
    total_phase_weeks: int,
) -> Tuple[str, str, List[str]]:
    progress = _phase_progress(phase_week, total_phase_weeks)
    primary_band, secondary_band = _band_emphasis_for_phase(race_distance, phase)
    final_targets = get_final_targets_for_event(race_distance)

    notes: List[str] = []

    if phase == "general":
        session_1 = get_general_session(race_distance, phase_week)
        session_2 = get_progression_session(race_distance, secondary_band, progress * 0.6)
        notes.append(
            f"General phase uses lower-key work plus early support at {secondary_band}% instead of jumping straight to end-state race sessions."
        )
    elif phase == "supportive":
        session_1 = get_progression_session(race_distance, primary_band, progress)
        session_2 = get_progression_session(race_distance, secondary_band, progress * 0.8)
        notes.append(
            f"Supportive phase advances toward the appendix target at {primary_band}%: {final_targets.get(primary_band, '')}."
        )
        notes.append(
            f"Secondary support also advances toward the appendix target at {secondary_band}%: {final_targets.get(secondary_band, '')}."
        )
    else:
        # specific phase: primary session pushes toward the culminating race-specific target
        session_1 = get_progression_session(race_distance, 100, progress)
        session_2 = get_progression_session(race_distance, secondary_band, progress)
        notes.append(
            f"Specific phase centers the week on progress toward the culminating 100% session: {final_targets.get(100, '')}."
        )
        if secondary_band in final_targets:
            notes.append(
                f"Secondary session keeps building the adjacent support rung at {secondary_band}%: {final_targets.get(secondary_band, '')}."
            )

    return session_1, session_2, notes


def _assign_week_sessions(
    week_number: int,
    phase: str,
    phase_week: int,
    total_phase_weeks: int,
    athlete: AthleteProfile,
    goal: GoalProfile,
    paces: Dict[int, Dict[str, str]],
    target_mileage: int,
    fitness_anchor_used: str,
    reanchored: bool = False,
) -> Dict:
    primary_hard, secondary_hard = hard_day_spacing(athlete.days_per_week, athlete.day_off)

    days = []
    phase_label = PHASE_NAMES[phase]

    long_run_miles = min(
        athlete.long_run_max,
        max(6, round(target_mileage * (0.24 if EVENT_CATEGORY[goal.race_distance] != "middle_distance" else 0.20))),
    )

    workout_1, workout_2, quality_notes = _build_quality_sessions_for_week(
        race_distance=goal.race_distance,
        phase=phase,
        phase_week=phase_week,
        total_phase_weeks=total_phase_weeks,
    )

    easy_miles = max(3, round((target_mileage - long_run_miles) / max(1, athlete.days_per_week - 1)))

    for day in DAY_ORDER:
        if day == athlete.day_off:
            session = "Off"
        elif day == primary_hard:
            session = workout_1
        elif day == secondary_hard:
            session = workout_2
        elif day == "Saturday" and athlete.day_off != "Saturday":
            session = get_long_run_description(goal.race_distance, long_run_miles, phase)
        else:
            include_strides = day in {"Monday", "Wednesday"} and phase != "specific"
            session = easy_run_description(easy_miles, include_strides=include_strides)

        days.append({"day": day, "session": session})

    notes = phase_notes(phase)
    notes.extend(_event_notes(goal.race_distance))
    notes.extend(quality_notes)

    if phase == "general":
        notes.append("Endurance support is still present because the source logic says endurance support matters more than speed support.")
    elif phase == "supportive":
        notes.append("This phase acts as the bridge from general work into the race-specific end-state sessions.")
    else:
        notes.append("Mileage is allowed to flatten or drop slightly here so the athlete can recover and feel fresh for the key sessions.")

    if reanchored:
        notes.append("This week was rebuilt from a manual fitness override instead of auto-updating behind the scenes.")

    return {
        "week_number": week_number,
        "phase": phase_label,
        "target_mileage": target_mileage,
        "days": days,
        "notes": notes,
        "fitness_anchor_used": fitness_anchor_used,
        "reanchored": reanchored,
    }


def _build_plan_from_anchor(
    athlete: AthleteProfile,
    goal: GoalProfile,
    anchor_distance: str,
    anchor_time: str,
) -> Dict:
    target_pace = get_target_pace_info(
        target_distance=goal.race_distance,
        current_distance=anchor_distance,
        current_time_str=anchor_time,
    )
    paces = get_percentage_paces(target_pace)

    phases = choose_phase_lengths(
        weeks_to_race=goal.weeks_to_race,
        experience=athlete.experience,
        max_mileage=athlete.max_mileage,
    )

    mileage_targets = weekly_mileage_targets(
        current_mileage=athlete.current_mileage,
        max_mileage=athlete.max_mileage,
       
