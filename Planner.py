from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List

import pandas as pd

from paces import (
    get_percentage_paces,
    get_target_pace_info,
    seconds_to_clock,
)
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
    general_workout,
    long_run_description,
    race_specific_workout,
    supportive_endurance_workout,
    supportive_speed_workout,
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


def _assign_week_sessions(
    week_number: int,
    phase: str,
    phase_week: int,
    athlete: AthleteProfile,
    goal: GoalProfile,
    paces: Dict[int, Dict[str, str]],
    target_mileage: int,
    fitness_anchor_used: str,
    reanchored: bool = False,
) -> Dict:
    event_category = EVENT_CATEGORY[goal.race_distance]
    primary_hard, secondary_hard = hard_day_spacing(athlete.days_per_week, athlete.day_off)

    days = []
    phase_label = PHASE_NAMES[phase]

    long_run_miles = min(
        athlete.long_run_max,
        max(6, round(target_mileage * (0.24 if event_category != "middle_distance" else 0.20))),
    )

    if phase == "general":
        workout_1 = general_workout(event_category, paces, phase_week)
        workout_2 = supportive_endurance_workout(event_category, paces, phase_week)
    elif phase == "supportive":
        workout_1 = supportive_endurance_workout(event_category, paces, phase_week)
        workout_2 = supportive_speed_workout(event_category, paces, phase_week)
    else:
        workout_1 = race_specific_workout(
            goal.race_distance,
            event_category,
            paces,
            phase_week,
            _phase_count(
                choose_phase_lengths(goal.weeks_to_race, athlete.experience, athlete.max_mileage),
                "specific",
            ),
        )
        workout_2 = supportive_endurance_workout(event_category, paces, phase_week)

    easy_miles = max(3, round((target_mileage - long_run_miles) / max(1, athlete.days_per_week - 1)))

    for day in DAY_ORDER:
        if day == athlete.day_off:
            session = "Off"
        elif day == primary_hard:
            session = workout_1
        elif day == secondary_hard:
            session = workout_2
        elif day == "Saturday" and athlete.day_off != "Saturday":
            session = long_run_description(event_category, paces, long_run_miles, phase)
        else:
            include_strides = day in {"Monday", "Wednesday"} and phase != "specific"
            session = easy_run_description(easy_miles, include_strides=include_strides)

        days.append({"day": day, "session": session})

    notes = phase_notes(phase)

    if phase == "general":
        notes.extend(
            [
                "Touches 100–115% in lower-key form instead of diving straight into heavy race-specific sessions.",
                "Keeps at least one endurance-oriented session in the week because endurance support should dominate.",
            ]
        )
    elif phase == "supportive":
        notes.extend(
            [
                "Uses 90% / 95% / 105% / 110% as stepping stones into race pace.",
                "Maintains general running around the harder sessions instead of replacing everything with workouts.",
            ]
        )
    else:
        notes.extend(
            [
                "Race-specific work is now more frequent.",
                "Mileage is allowed to flatten or drop slightly so the athlete can recover and feel fresh.",
            ]
        )

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
        weeks_to_race=goal.weeks_to_race,
        phases=phases,
    )

    fitness_anchor_used = f"{anchor_distance} in {anchor_time}"

    weeks: List[Dict] = []
    for idx, phase in enumerate(phases):
        week_number = idx + 1
        phase_week = _week_in_phase(phases, idx)
        week = _assign_week_sessions(
            week_number=week_number,
            phase=phase,
            phase_week=phase_week,
            athlete=athlete,
            goal=goal,
            paces=paces,
            target_mileage=mileage_targets[idx],
            fitness_anchor_used=fitness_anchor_used,
            reanchored=False,
        )
        weeks.append(week)

    phase_counts = {
        "general": phases.count("general"),
        "supportive": phases.count("supportive"),
        "specific": phases.count("specific"),
    }

    summary = {
        "race_distance": goal.race_distance,
        "fitness_anchor": fitness_anchor_used,
        "phase_structure": (
            f"{phase_counts['general']} general / "
            f"{phase_counts['supportive']} supportive / "
            f"{phase_counts['specific']} specific"
        ),
        "peak_mileage": max(mileage_targets),
        "estimated_target_time": seconds_to_clock(target_pace.time_seconds),
        "override_applied": None,
    }

    notes = [
        "Uses current fitness as the anchor, not goal fitness.",
        "Builds the pace ladder from 80% to 115% of race pace.",
        "Biases the plan toward endurance support more than speed support.",
        "Places race-specific work before supportive and general work in the planning logic.",
        "Allows mileage to level off or taper in the specific phase.",
    ]

    return {
        "summary": summary,
        "paces": paces,
        "paces_df": _pace_table_df(paces),
        "weeks": weeks,
        "notes": notes,
    }


def build_training_plan(athlete: AthleteProfile, goal: GoalProfile) -> Dict:
    return _build_plan_from_anchor(
        athlete=athlete,
        goal=goal,
        anchor_distance=athlete.current_distance,
        anchor_time=athlete.current_time,
    )


def apply_manual_fitness_override(
    existing_plan: Dict,
    athlete: AthleteProfile,
    goal: GoalProfile,
    override_distance: str,
    override_time: str,
    rebuild_start_week: int,
) -> Dict:
    """
    Keep weeks before rebuild_start_week from the original plan.
    Rebuild weeks from rebuild_start_week onward using the manual override anchor.
    """
    if rebuild_start_week < 1 or rebuild_start_week > goal.weeks_to_race:
        raise ValueError("rebuild_start_week is out of range.")

    override_plan = _build_plan_from_anchor(
        athlete=replace(athlete, current_distance=override_distance, current_time=override_time),
        goal=goal,
        anchor_distance=override_distance,
        anchor_time=override_time,
    )

    preserved_weeks = []
    for week in existing_plan["weeks"]:
        if week["week_number"] < rebuild_start_week:
            preserved_weeks.append(week)

    rebuilt_weeks = []
    for week in override_plan["weeks"]:
        if week["week_number"] >= rebuild_start_week:
            week_copy = dict(week)
            week_copy["reanchored"] = True
            week_copy["fitness_anchor_used"] = f"{override_distance} in {override_time}"
            rebuilt_weeks.append(week_copy)

    merged_weeks = preserved_weeks + rebuilt_weeks

    merged_plan = {
        "summary": dict(existing_plan["summary"]),
        "paces": override_plan["paces"],
        "paces_df": override_plan["paces_df"],
        "weeks": merged_weeks,
        "notes": list(existing_plan["notes"]),
    }

    merged_plan["summary"]["override_applied"] = (
        f"{override_distance} in {override_time}, from week {rebuild_start_week}"
    )

    merged_plan["notes"].append(
        f"Manual override applied from week {rebuild_start_week} using {override_distance} in {override_time}."
    )
    merged_plan["notes"].append(
        "Earlier weeks are preserved; later weeks are rebuilt from the new fitness anchor."
    )

    return merged_plan
