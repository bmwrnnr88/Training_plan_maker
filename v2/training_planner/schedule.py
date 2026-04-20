from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional

from load_model import classify_load, compute_load
from models import Phase, PlannerResult, ScheduleEntry, SessionRecord
from planner import generate_next_workout
from workouts_5k import WORKOUT_DB_5K

ROLLING_PATTERNS = {
    "general": [
        "quality",
        "recovery",
        "support",
        "easy",
        "quality",
        "recovery",
        "long_support",
        "easy",
        "quality",
        "recovery",
        "support",
        "easy",
        "quality",
        "long_support",
    ],
    "supportive": [
        "quality",
        "recovery",
        "support",
        "quality",
        "recovery",
        "long_support",
        "easy",
        "quality",
        "recovery",
        "support",
        "quality",
        "recovery",
        "long_support",
        "off",
    ],
    "specific": [
        "quality",
        "recovery",
        "support",
        "quality",
        "recovery",
        "long_support",
        "easy",
        "quality",
        "recovery",
        "support",
        "quality",
        "recovery",
        "long_support",
        "off",
    ],
}


def _parse_local_date(raw_date: str) -> date:
    return datetime.strptime(raw_date, "%Y-%m-%d").date()


def _find_workout_by_id(workout_id: str):
    return next(workout for workout in WORKOUT_DB_5K if workout.id == workout_id)


def _session_record_from_schedule_entry(entry: ScheduleEntry) -> Optional[SessionRecord]:
    if entry.primary_percent is None or entry.session_type == "off":
        return None

    normalized_status = entry.status
    if normalized_status == "missed":
        return None

    completion_ratio = min(max(entry.completion_ratio, 0.0), 1.0)
    if normalized_status == "planned" or completion_ratio <= 0.0:
        return None

    equivalent_volume_m = int(round(entry.equivalent_volume_m * completion_ratio))
    load_score = round(entry.load_estimate * completion_ratio, 1)
    if load_score <= 0 and entry.primary_percent is not None:
        load_score = compute_load({entry.primary_percent: 20.0 * completion_ratio}, 0.0)

    mechanical_flag = "low"
    if entry.primary_percent >= 110:
        mechanical_flag = "high"
    elif entry.primary_percent >= 100:
        mechanical_flag = "medium"

    return SessionRecord(
        date=entry.date,
        primary_percent=entry.primary_percent,
        secondary_percents=entry.secondary_percents,
        workout_text=entry.workout_text,
        equivalent_volume_m=equivalent_volume_m,
        load_score=load_score,
        load_class=classify_load(load_score),
        mechanical_flag=mechanical_flag,
    )


def _schedule_history(existing_entries: Iterable[ScheduleEntry], start_date: date) -> List[SessionRecord]:
    history: List[SessionRecord] = []

    for entry in existing_entries:
        try:
            entry_date = _parse_local_date(entry.date)
        except ValueError:
            continue
        if entry_date >= start_date:
            continue
        session_record = _session_record_from_schedule_entry(entry)
        if session_record is not None:
            history.append(session_record)

    return history


def _next_schedule_start(existing_entries: Iterable[ScheduleEntry]) -> date:
    today = date.today()
    today_logged = any(
        entry.date == today.isoformat() and entry.status in {"completed", "partial", "missed"}
        for entry in existing_entries
    )
    return today + timedelta(days=1) if today_logged else today


def _pace_fragment(percent: int, pace_ladder: Optional[Dict[int, Dict[str, float | str]]]) -> str:
    if pace_ladder is None:
        return f"{percent}%"
    return f"{pace_ladder[percent]['pace_per_mile']}/mi ({pace_ladder[percent]['pace_per_km']}/km)"


def _equivalent_volume_from_minutes(
    percent: int,
    minutes: float,
    pace_ladder: Optional[Dict[int, Dict[str, float | str]]],
) -> int:
    if pace_ladder is None:
        return int(round(minutes * 160.0))
    seconds_per_mile = float(pace_ladder[percent]["seconds_per_mile"])
    miles = (minutes * 60.0) / seconds_per_mile
    return int(round(miles * 1609.344))


def _support_entry(
    session_date: date,
    session_type: str,
    phase: Phase,
    pace_ladder: Optional[Dict[int, Dict[str, float | str]]],
) -> ScheduleEntry:
    if session_type == "recovery":
        percent = 80
        minutes = 35.0
        workout_text = f"35 min easy at 80% around {_pace_fragment(percent, pace_ladder)}"
        reason = "recovery support between higher-cost sessions"
    elif session_type == "support":
        if phase == "general":
            percent = 85
            minutes = 45.0
            workout_text = (
                f"45 min at 85% around {_pace_fragment(percent, pace_ladder)}"
                " with 6 x 20 sec relaxed strides if feeling good"
            )
        elif phase == "supportive":
            percent = 90
            minutes = 45.0
            workout_text = f"45 min at 90% around {_pace_fragment(percent, pace_ladder)}"
        else:
            percent = 85
            minutes = 40.0
            workout_text = (
                f"40 min at 85% around {_pace_fragment(percent, pace_ladder)}"
                f" plus 6 x 20 sec relaxed strides near {_pace_fragment(115, pace_ladder)}"
            )
        reason = "supportive aerobic work to connect the quality days"
    elif session_type == "long_support":
        if phase == "general":
            percent = 80
            minutes = 80.0
            workout_text = (
                f"80 min mostly at 80% around {_pace_fragment(80, pace_ladder)}"
                f" with the last 10-15 min around {_pace_fragment(85, pace_ladder)}"
            )
        elif phase == "supportive":
            percent = 80
            minutes = 75.0
            workout_text = (
                f"75 min mostly at 80% around {_pace_fragment(80, pace_ladder)}"
                f" with the last 15 min around {_pace_fragment(85, pace_ladder)}"
            )
        else:
            percent = 80
            minutes = 70.0
            workout_text = (
                f"70 min mostly at 80% around {_pace_fragment(80, pace_ladder)}"
                f" with the last 15 min around {_pace_fragment(90, pace_ladder)}"
            )
        reason = "longer support run that keeps endurance carrying the schedule"
    elif session_type == "easy":
        percent = 80
        minutes = 40.0
        workout_text = f"40 min easy at 80% around {_pace_fragment(percent, pace_ladder)} or shorten if tired"
        reason = "low-cost aerobic day to keep the week moving"
    else:
        return ScheduleEntry(
            date=session_date.isoformat(),
            day_label=session_date.strftime("%a"),
            session_type="off",
            primary_percent=None,
            secondary_percents=[],
            workout_text="Rest day or 20-30 min very easy if you need to loosen up",
            equivalent_volume_m=0,
            load_estimate=0.0,
            load_class="easy",
            reason_summary="intentional down day to leave room for the next quality session",
        )

    load_estimate = compute_load({percent: minutes}, 0.0)
    return ScheduleEntry(
        date=session_date.isoformat(),
        day_label=session_date.strftime("%a"),
        session_type=session_type,
        primary_percent=percent,
        secondary_percents=[],
        workout_text=workout_text,
        equivalent_volume_m=_equivalent_volume_from_minutes(percent, minutes, pace_ladder),
        load_estimate=load_estimate,
        load_class=classify_load(load_estimate),
        reason_summary=reason,
    )


def _quality_entry(
    session_date: date,
    result: PlannerResult,
) -> ScheduleEntry:
    selected_workout = _find_workout_by_id(result.selected_workout_id)
    return ScheduleEntry(
        date=session_date.isoformat(),
        day_label=session_date.strftime("%a"),
        session_type="quality",
        primary_percent=result.selected_percent,
        secondary_percents=result.secondary_percents,
        workout_text=result.workout_text,
        equivalent_volume_m=selected_workout.equivalent_volume_m,
        load_estimate=result.load_estimate,
        load_class=result.load_class,
        reason_summary=result.reason_summary,
    )


def generate_two_week_schedule(
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
    pace_ladder: Optional[Dict[int, Dict[str, float | str]]] = None,
    existing_entries: Optional[Iterable[ScheduleEntry]] = None,
) -> List[ScheduleEntry]:
    """Build a rolling 14-day schedule and adapt it to logged schedule outcomes."""
    existing_entries = list(existing_entries or [])
    start_date = _next_schedule_start(existing_entries)
    simulated_history = list(history) + _schedule_history(existing_entries, start_date)
    pattern = ROLLING_PATTERNS[phase]
    schedule: List[ScheduleEntry] = []

    for day_offset, session_type in enumerate(pattern):
        session_date = start_date + timedelta(days=day_offset)
        if session_type == "quality":
            result = generate_next_workout(
                phase=phase,
                capacities=capacities,
                history=simulated_history,
                readiness=readiness,
            )
            entry = _quality_entry(session_date, result)
        else:
            entry = _support_entry(session_date, session_type, phase, pace_ladder)

        schedule.append(entry)

        session_record = _session_record_from_schedule_entry(
            ScheduleEntry(**{**asdict(entry), "status": "completed", "completion_ratio": 1.0})
        )
        if session_record is not None:
            simulated_history.append(session_record)

    return schedule
