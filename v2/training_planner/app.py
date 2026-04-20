from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
import os
from typing import Dict, List
import pandas as pd
import streamlit as st

from capacity import normalize_capacity
from config import PEAK_EQUIVALENTS_5K
from intervals_icu import IntervalsImportResult, import_recent_history
from load_model import classify_load
from models import PlannerResult, ScheduleEntry, SessionRecord
from paces import get_percentage_paces
from planner import generate_next_workout
from schedule import generate_two_week_schedule
from utils import (
    capacity_table,
    format_equivalent_volume,
    format_percent,
    format_secondary_percents,
    meters_to_miles,
    miles_to_meters,
    peak_workout_references,
)

PERCENT_RUNG_ORDER = [80, 85, 90, 95, 100, 105, 110, 115]
DEFAULT_COMPLETED_EQUIVALENTS_M = {
    80: 13277,
    85: 7242,
    90: 5069,
    95: 4000,
    100: 2520,
    105: 1800,
    110: 800,
    115: 600,
}


def _default_history_rows() -> List[dict]:
    today = date.today()
    return [
        {
            "date": (today - timedelta(days=6)).isoformat(),
            "primary_percent": 90,
            "secondary_percents": "",
            "workout_text": "4 miles at 90%",
            "equivalent_volume_m": 6437,
            "load_score": 24.5,
            "load_class": "moderate",
            "mechanical_flag": "low",
        },
        {
            "date": (today - timedelta(days=3)).isoformat(),
            "primary_percent": 115,
            "secondary_percents": "",
            "workout_text": "8 x 100m strides / fast relaxed sprints",
            "equivalent_volume_m": 800,
            "load_score": 6.5,
            "load_class": "easy",
            "mechanical_flag": "high",
        },
    ]


def _parse_secondary_percents(raw_value: str) -> List[int]:
    values: List[int] = []
    for token in str(raw_value).split(","):
        cleaned = token.strip()
        if not cleaned:
            continue
        try:
            values.append(int(cleaned))
        except ValueError:
            continue
    return values


def _history_records_from_editor(history_df: pd.DataFrame) -> List[SessionRecord]:
    records: List[SessionRecord] = []

    for row in history_df.fillna("").to_dict(orient="records"):
        date_value = str(row.get("date", "")).strip()
        workout_text = str(row.get("workout_text", "")).strip()
        if not date_value or not workout_text:
            continue

        try:
            primary_percent = int(row.get("primary_percent", 0))
            equivalent_volume = int(float(row.get("equivalent_volume_m", 0)))
            load_score = float(row.get("load_score", 0.0))
        except (TypeError, ValueError):
            continue

        records.append(
            SessionRecord(
                date=date_value,
                primary_percent=primary_percent,
                secondary_percents=_parse_secondary_percents(str(row.get("secondary_percents", ""))),
                workout_text=workout_text,
                equivalent_volume_m=equivalent_volume,
                load_score=load_score,
                load_class=str(row.get("load_class", "easy")) or "easy",
                mechanical_flag=str(row.get("mechanical_flag", "low")) or "low",
            )
        )

    return records


def _merge_history_rows(
    existing_rows: List[dict],
    imported_rows: List[dict],
    replace_existing: bool,
) -> List[dict]:
    if replace_existing:
        return imported_rows

    merged: List[dict] = []
    seen = set()
    for row in imported_rows + existing_rows:
        key = (str(row.get("date", "")), str(row.get("workout_text", "")))
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    merged.sort(key=lambda row: str(row.get("date", "")), reverse=True)
    return merged


def _render_result(result: PlannerResult) -> None:
    st.subheader("Next Workout")
    st.markdown(f"**Primary percent:** {format_percent(result.selected_percent)}")
    st.markdown(
        f"**Secondary percents:** {format_secondary_percents(result.secondary_percents)}"
    )
    st.markdown(f"**Workout:** {result.workout_text}")
    st.markdown(f"**Load estimate:** {result.load_estimate:.1f}")
    st.markdown(f"**Load class:** {result.load_class}")
    st.markdown(f"**Reason summary:** {result.reason_summary}")


def _pace_ladder_df(paces: Dict[int, Dict[str, float | str]]) -> pd.DataFrame:
    """Render the fixed percent pace ladder."""
    rows = [
        {
            "Percent": format_percent(percent),
            "Pace / mile": data["pace_per_mile"],
            "Pace / km": data["pace_per_km"],
        }
        for percent, data in paces.items()
    ]
    return pd.DataFrame(rows)


def _default_intervals_api_key() -> str:
    """Load the Intervals.icu key from env or Streamlit secrets when available."""
    env_value = os.environ.get("INTERVALS_ICU_API_KEY", "").strip()
    if env_value:
        return env_value
    try:
        secret_value = str(st.secrets.get("INTERVALS_ICU_API_KEY", "")).strip()
    except Exception:
        secret_value = ""
    return secret_value


def _schedule_rows_for_editor(entries: List[ScheduleEntry]) -> List[dict]:
    rows = []
    for entry in entries:
        row = asdict(entry)
        row["secondary_percents"] = ", ".join(str(percent) for percent in entry.secondary_percents)
        rows.append(row)
    return rows


def _schedule_entries_from_editor(schedule_df: pd.DataFrame) -> List[ScheduleEntry]:
    entries: List[ScheduleEntry] = []
    for row in schedule_df.fillna("").to_dict(orient="records"):
        date_value = str(row.get("date", "")).strip()
        workout_text = str(row.get("workout_text", "")).strip()
        session_type = str(row.get("session_type", "off")).strip() or "off"
        if not date_value or not workout_text:
            continue

        primary_raw = row.get("primary_percent", "")
        try:
            primary_percent = int(primary_raw) if str(primary_raw).strip() else None
        except (TypeError, ValueError):
            primary_percent = None

        try:
            equivalent_volume_m = int(float(row.get("equivalent_volume_m", 0)))
            load_estimate = float(row.get("load_estimate", 0.0))
            completion_ratio = float(row.get("completion_ratio", 1.0))
        except (TypeError, ValueError):
            continue

        entries.append(
            ScheduleEntry(
                date=date_value,
                day_label=str(row.get("day_label", "")).strip() or date_value,
                session_type=session_type,  # type: ignore[arg-type]
                primary_percent=primary_percent,
                secondary_percents=_parse_secondary_percents(str(row.get("secondary_percents", ""))),
                workout_text=workout_text,
                equivalent_volume_m=equivalent_volume_m,
                load_estimate=load_estimate,
                load_class=str(row.get("load_class", "easy")) or "easy",
                reason_summary=str(row.get("reason_summary", "")).strip(),
                status=str(row.get("status", "planned")) or "planned",
                completion_ratio=completion_ratio,
            )
        )
    return entries


def _import_preview_df(import_result: IntervalsImportResult) -> pd.DataFrame:
    preview_rows = [
        {
            "Date": row["date"],
            "Primary %": format_percent(int(row["primary_percent"])),
            "Workout": row["workout_text"],
            "Equivalent": format_equivalent_volume(int(row["equivalent_volume_m"])),
            "Load": f"{float(row['load_score']):.1f}",
        }
        for row in import_result.imported_rows
    ]
    return pd.DataFrame(preview_rows)


def main() -> None:
    """Render the Streamlit percentage-based 5K planner."""
    st.set_page_config(page_title="Percentage-Based 5K Planner", layout="wide")
    st.title("Percentage-Based 5K Planner")
    st.caption("A 5K-only planner that stays in percentage-based vocabulary.")

    if "history_rows" not in st.session_state:
        st.session_state["history_rows"] = _default_history_rows()
    if "schedule_rows" not in st.session_state:
        st.session_state["schedule_rows"] = []
    if "last_intervals_import" not in st.session_state:
        st.session_state["last_intervals_import"] = None

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Inputs")
        phase = st.selectbox("Phase", options=["general", "supportive", "specific"], index=0)
        readiness = st.select_slider("Readiness", options=[1, 2, 3, 4, 5], value=3)
        current_5k_time = st.text_input(
            "Current 5K time anchor (mm:ss or hh:mm:ss)",
            value="20:00",
        )

        pace_ladder = None
        try:
            pace_ladder = get_percentage_paces(current_5k_time)
        except ValueError as exc:
            st.warning(f"Pace ladder unavailable: {exc}")

        with st.expander("Intervals.icu Import", expanded=False):
            st.caption(
                "Imports recent completed run activities using your personal API key and maps them"
                " into editable planner history rows."
            )
            intervals_api_key = st.text_input(
                "Intervals.icu API key",
                type="password",
                value=_default_intervals_api_key(),
            )
            athlete_id = st.text_input(
                "Athlete ID (leave blank to use the athlete tied to the API key)",
                value="",
            ).strip()
            import_days = st.slider("Days of recent history to import", min_value=7, max_value=42, value=21)
            replace_history = st.checkbox("Replace current history editor with imported rows", value=False)
            if st.button("Import Recent Intervals.icu Activities", use_container_width=True):
                if not intervals_api_key:
                    st.warning("Enter your Intervals.icu API key first.")
                else:
                    try:
                        import_result = import_recent_history(
                            api_key=intervals_api_key,
                            athlete_id=athlete_id or None,
                            days=import_days,
                            current_5k_time=current_5k_time,
                        )
                    except ValueError as exc:
                        st.session_state["last_intervals_import"] = None
                        st.error(str(exc))
                    else:
                        imported_rows = import_result.imported_rows
                        st.session_state["history_rows"] = _merge_history_rows(
                            existing_rows=st.session_state["history_rows"],
                            imported_rows=imported_rows,
                            replace_existing=replace_history,
                        )
                        st.session_state["last_intervals_import"] = import_result
                        if imported_rows:
                            st.success(f"Imported {len(imported_rows)} recent run activities.")
                        else:
                            st.warning(
                                "No recent run activities were imported. The recent Intervals.icu entries looked"
                                " like notes, calendar items, non-run sessions, or activities missing the fields"
                                " needed for mapping."
                            )

            last_import = st.session_state.get("last_intervals_import")
            if last_import is not None:
                st.caption(
                    "Import summary:"
                    f" scanned {last_import.scanned_entries} recent entries,"
                    f" found {last_import.candidate_activities} completed activities,"
                    f" imported {len(last_import.imported_rows)} runs,"
                    f" skipped {last_import.skipped_note_entries} note/calendar entries,"
                    f" {last_import.skipped_non_runs} non-run activities,"
                    f" and {last_import.skipped_missing_fields} activities with missing fields."
                )
                if last_import.imported_rows:
                    st.dataframe(
                        _import_preview_df(last_import),
                        use_container_width=True,
                        hide_index=True,
                    )

        st.markdown("**Current Completed Equivalent by Percent**")
        st.caption(
            "Enter the amount the athlete can currently handle at each rung as equivalent volume."
            " Example: 4.0 miles completed at a rung whose peak is 7.0 miles."
            " If a rung has both continuous and interval options, just enter the best current equivalent volume."
        )
        capacities: Dict[int, float] = {}
        completed_equivalents_m: Dict[int, int] = {}
        capacity_columns = st.columns(4)
        for index, percent in enumerate(PERCENT_RUNG_ORDER):
            with capacity_columns[index % 4]:
                default_miles = meters_to_miles(DEFAULT_COMPLETED_EQUIVALENTS_M[percent])
                completed_miles = st.number_input(
                    f"{percent}% equivalent",
                    min_value=0.0,
                    value=float(round(default_miles, 2)),
                    step=0.1,
                    format="%.2f",
                )
                completed_equivalents_m[percent] = min(
                    miles_to_meters(completed_miles),
                    PEAK_EQUIVALENTS_5K[percent],
                )
                capacities[percent] = normalize_capacity(
                    percent,
                    completed_equivalents_m[percent],
                )
                st.caption(
                    f"Peak: {format_equivalent_volume(PEAK_EQUIVALENTS_5K[percent])}"
                )

        st.dataframe(
            capacity_table(completed_equivalents_m, capacities),
            use_container_width=True,
            hide_index=True,
        )

        if pace_ladder is not None:
            with st.expander("Percent Paces", expanded=True):
                st.caption("These paces are anchored to the current 5K mark above.")
                st.dataframe(
                    _pace_ladder_df(pace_ladder),
                    use_container_width=True,
                    hide_index=True,
                )

        with st.expander("Peak Workout References", expanded=False):
            st.caption(
                "Peak means the actual peak workout target at that rung. Top-down, bottom-up, and alternation"
                " are routes toward that peak. Blends are connector workouts that link adjacent stimuli and"
                " support specific work, not separate peak definitions."
            )
            for percent in PERCENT_RUNG_ORDER:
                references = peak_workout_references(percent)
                st.markdown(
                    f"**{format_percent(percent)} peak:** {format_equivalent_volume(PEAK_EQUIVALENTS_5K[percent])}"
                )
                for reference in references["peak_targets"]:
                    st.markdown(
                        f"- `Peak target · {reference['style']}`: {reference['workout_text']} "
                        f"({format_equivalent_volume(reference['equivalent_volume_m'])})"
                    )
                for reference in references["peak_builders"]:
                    st.markdown(
                        f"- `Build toward peak · {reference['style']}`: {reference['workout_text']} "
                        f"({format_equivalent_volume(reference['equivalent_volume_m'])})"
                    )
                for reference in references["blend_support"]:
                    st.markdown(
                        f"- `Blend support · {reference['style']}`: {reference['workout_text']} "
                        f"({format_equivalent_volume(reference['equivalent_volume_m'])})"
                    )

    with col_right:
        st.subheader("Recent History")
        history_df = pd.DataFrame(st.session_state["history_rows"])
        edited_history = st.data_editor(
            history_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.TextColumn("Date"),
                "primary_percent": st.column_config.NumberColumn(
                    "Primary percent", min_value=80, max_value=115, step=5
                ),
                "secondary_percents": st.column_config.TextColumn(
                    "Secondary percents"
                ),
                "workout_text": st.column_config.TextColumn("Workout text", width="large"),
                "equivalent_volume_m": st.column_config.NumberColumn(
                    "Equivalent volume", min_value=0, step=100
                ),
                "load_score": st.column_config.NumberColumn(
                    "Load score", min_value=0.0, step=0.5, format="%.1f"
                ),
                "load_class": st.column_config.SelectboxColumn(
                    "Load class",
                    options=["easy", "moderate", "hard", "very_hard"],
                ),
                "mechanical_flag": st.column_config.SelectboxColumn(
                    "Mechanical flag",
                    options=["low", "medium", "high"],
                ),
            },
        )
        st.session_state["history_rows"] = edited_history.to_dict(orient="records")

    history_records = _history_records_from_editor(edited_history)

    if history_records:
        st.markdown("---")
        st.subheader("History Snapshot")
        latest_session = history_records[0]
        st.write(
            "Most recent entry:",
            latest_session.date,
            format_percent(latest_session.primary_percent),
            latest_session.workout_text,
            f"({classify_load(latest_session.load_score)})",
        )

    st.markdown("---")
    st.subheader("Rolling 2-Week Schedule")
    st.caption(
        "Build a rolling 14-day schedule, then mark sessions as completed, partial, or missed."
        " Refreshing the schedule folds the logged outcomes back into planner history."
    )

    schedule_df = pd.DataFrame(st.session_state["schedule_rows"])
    current_schedule_entries: List[ScheduleEntry] = []
    if not schedule_df.empty:
        edited_schedule = st.data_editor(
            schedule_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Date", disabled=True),
                "day_label": st.column_config.TextColumn("Day", disabled=True),
                "session_type": st.column_config.TextColumn("Session type", disabled=True),
                "primary_percent": st.column_config.NumberColumn("Primary %", disabled=True),
                "secondary_percents": st.column_config.TextColumn("Secondary %", disabled=True),
                "workout_text": st.column_config.TextColumn("Session", disabled=True, width="large"),
                "equivalent_volume_m": st.column_config.NumberColumn("Eq. m", disabled=True),
                "load_estimate": st.column_config.NumberColumn("Load", disabled=True, format="%.1f"),
                "load_class": st.column_config.TextColumn("Load class", disabled=True),
                "reason_summary": st.column_config.TextColumn("Why", disabled=True, width="large"),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["planned", "completed", "partial", "missed"],
                ),
                "completion_ratio": st.column_config.NumberColumn(
                    "Completion",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.1,
                    format="%.1f",
                ),
            },
        )
        st.session_state["schedule_rows"] = edited_schedule.to_dict(orient="records")
        current_schedule_entries = _schedule_entries_from_editor(edited_schedule)

        first_quality = next(
            (entry for entry in current_schedule_entries if entry.session_type == "quality"),
            None,
        )
        if first_quality is not None:
            next_workout_result = PlannerResult(
                selected_percent=first_quality.primary_percent or 80,
                selected_workout_id="schedule_preview",
                workout_text=first_quality.workout_text,
                secondary_percents=first_quality.secondary_percents,
                load_estimate=first_quality.load_estimate,
                load_class=first_quality.load_class,
                reason_summary=first_quality.reason_summary,
            )
            _render_result(next_workout_result)
            if pace_ladder is not None and first_quality.primary_percent is not None:
                st.markdown(
                    f"**Primary percent pace:** {pace_ladder[first_quality.primary_percent]['pace_per_mile']}/mi"
                    f" | {pace_ladder[first_quality.primary_percent]['pace_per_km']}/km"
                )

    if st.button("Build / Refresh 2-Week Schedule", type="primary", use_container_width=True):
        try:
            schedule_entries = generate_two_week_schedule(
                phase=phase,
                capacities=capacities,
                history=history_records,
                readiness=readiness,
                pace_ladder=pace_ladder,
                existing_entries=current_schedule_entries,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["schedule_rows"] = _schedule_rows_for_editor(schedule_entries)
            st.success("Built a refreshed 2-week schedule. Update statuses and refresh again as training happens.")


if __name__ == "__main__":
    main()
