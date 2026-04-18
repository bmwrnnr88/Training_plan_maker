from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional

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
    FINAL_TARGETS,
    easy_run_description,
    long_run_description,
    general_filler_workout,
    build_progression_session,
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


def _phase_total(phases: List[str], phase_name: str) -> int:
    return phases.count(phase_name)


def _build_key_session_maps(
    goal: GoalProfile,
    athlete: AthleteProfile,
    paces: Dict[int, Dict[str, str]],
    phases: List[str],
) -> Dict[int, Dict[str, Optional[str]]]:
    event = goal.race_distance
    if event not in FINAL_TARGETS:
        raise ValueError(f"No FINAL_TARGETS entry found for {event} in workouts.py")

    week_map: Dict[int, Dict[str, Optional[str]]] = {}

    general_total = _phase_total(phases, "general")
    supportive_total = _phase_total(phases, "supportive")
    specific_total = _phase_total(phases, "specific")

    for idx, phase in enumerate(phases):
        week_num = idx + 1
        phase_week = _week_in_phase(phases, idx)

        primary: Optional[str] = None
        secondary: Optional[str] = None

        if phase == "general":
            primary = general_filler_workout(
                race_distance=event,
                event_category=EVENT_CATEGORY[event],
                paces=paces,
                phase_week=phase_week,
                phase_total=general_total,
            )
            secondary = build_progression_session(
                race_distance=event,
                band=90,
                paces=paces,
                step_index=phase_week,
                total_steps=max(1, general_total),
                athlete_mileage=athlete.max_mileage,
            )

        elif phase == "supportive":
            if phase_week % 2 == 1:
                primary_band = 90
                secondary_band = 110
            else:
                primary_band = 95
                secondary_band = 105

            primary = build_progression_session(
                race_distance=event,
                band=primary_band,
                paces=paces,
                step_index=phase_week,
                total_steps=max(1, supportive_total),
                athlete_mileage=athlete.max_mileage,
            )
            secondary = build_progression_session(
                race_distance=event,
                band=secondary_band,
                paces=paces,
                step_index=phase_week,
                total_steps=max(1, supportive_total),
                athlete_mileage=athlete.max_mileage,
            )

        else:
            targets = FINAL_TARGETS[event]

            if phase_week == specific_total and 100 in targets:
                primary_band = 100
            elif phase_week == max(1, specific_total - 1) and 105 in targets:
                primary_band = 105
            else:
                primary_band = 100 if 100 in targets else 95

            secondary_band = 95 if 95 in targets else 90

            primary = build_progression_session(
                race_distance=event,
                band=primary_band,
                paces=paces,
                step_index=phase_week,
                total_steps=max(1, specific_total),
                athlete_mileage=athlete.max_mileage,
            )
            secondary = build_progression_session(
                race_distance=event,
                band=secondary_band,
                paces=paces,
                step_index=phase_week,
                total_steps=max(1, specific_total),
                athlete_mileage=athlete.max_mileage,
            )

        week_map[week_num] = {
            "primary": primary,
            "secondary": secondary,
        }

    return week_map


def _easy_miles_for_week(
    target_mileage: int,
    long_run_miles: int,
    days_per_week: int,
    doubles: bool,
) -> int:
    divisor = max(1, days_per_week - 1)
    if doubles:
        divisor += 1
    return max(3, round((target_mileage - long_run_miles) / divisor))


def _assign_week_sessions(
    week_number: int,
    phase: str,
    athlete: AthleteProfile,
    goal: GoalProfile,
    paces: Dict[int, Dict[str, str]],
    target_mileage: int,
    key_sessions: Dict[str, Optional[str]],
    fitness_anchor_used: str,
    reanchored: bool = False,
) -> Dict:
    event_category = EVENT_CATEGORY[goal.race_distance]
    primary_hard, secondary_hard = hard_day_spacing(athlete.days_per_week, athlete.day_off)

    long_run_miles = min(
        athlete.long_run_max,
        max(6, round(target_mileage * (0.24 if event_category != "middle_distance" else 0.20))),
    )

    easy_miles = _easy_miles_for_week(
        target_mileage=target_mileage,
        long_run_miles=long_run_miles,
        days_per_week=athlete.days_per_week,
        doubles=athlete.doubles,
    )

    days = []
    for day in DAY_ORDER:
        if day == athlete.day_off:
            session = "Off"
        elif day == primary_hard:
            session = key_sessions["primary"] or easy_run_description(easy_miles)
        elif day == secondary_hard:
            session = key_sessions["secondary"] or easy_run_description(easy_miles)
        elif day == "Saturday" and athlete.day_off != "Saturday":
            session = long_run_description(
                race_distance=goal.race_distance,
                event_category=event_category,
                paces=paces,
                long_run_miles=long_run_miles,
                phase=phase,
            )
        else:
            include_strides = day in {"Monday", "Wednesday"} and phase != "specific"
            session = easy_run_description(easy_miles, include_strides=include_strides)

        days.append({"day": day, "session": session})

    notes = phase_notes(phase)

    if phase == "general":
        notes.extend(
            [
                "General phase keeps the work lower-key but still touches relevant speeds.",
                "Endurance support is already present instead of waiting until late in the cycle.",
            ]
        )
    elif phase == "supportive":
        notes.extend(
            [
                "Supportive phase builds the bridge toward the final 95/100/105 sessions.",
                "90% and 110% are used as support rungs, not random extras.",
            ]
        )
    else:
        notes.extend(
            [
                "Race-specific work becomes more prominent and more frequent later in training.",
                "Mileage can flatten or drop slightly here so recovery supports the key sessions.",
            ]
        )

    if reanchored:
        notes.append("This week was rebuilt from a manual fitness override.")

    return {
        "week_number": week_number,
        "phase": PHASE_NAMES[phase],
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

    key_session_map = _build_key_session_maps(
        goal=goal,
        athlete=athlete,
        paces=paces,
        phases=phases,
    )

    fitness_anchor_used = f"{anchor_distance} in {anchor_time}"
    weeks: List[Dict] = []

    for idx, phase in enumerate(phases):
        week_number = idx + 1
        week = _assign_week_sessions(
            week_number=week_number,
            phase=phase,
            athlete=athlete,
            goal=goal,
            paces=paces,
            target_mileage=mileage_targets[idx],
            key_sessions=key_session_map[week_number],
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
        "Uses current fitness as the anchor.",
        "Builds the plan backward from key sessions instead of rotating generic workouts.",
        "Uses adjacent pace bands as a ladder of support around the target race.",
        "Weights endurance support more heavily than speed support.",
        "Lets mileage serve the progression of workouts.",
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
    if rebuild_start_week < 1 or rebuild_start_week > goal.weeks_to_race:
        raise ValueError("rebuild_start_week is out of range.")

    override_plan = _build_plan_from_anchor(
        athlete=replace(athlete, current_distance=override_distance, current_time=override_time),
        goal=goal,
        anchor_distance=override_distance,
        anchor_time=override_time,
    )

    preserved_weeks = [w for w in existing_plan["weeks"] if w["week_number"] < rebuild_start_week]
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
