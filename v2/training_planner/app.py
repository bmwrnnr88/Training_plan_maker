from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st

from capacity import normalize_capacity
from config import PEAK_EQUIVALENTS_5K
from load_model import classify_load
from models import PlannerResult, SessionRecord
from paces import get_percentage_paces
from planner import generate_next_workout
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


def main() -> None:
    """Render the Streamlit percentage-based 5K planner."""
    st.set_page_config(page_title="Percentage-Based 5K Planner", layout="wide")
    st.title("Percentage-Based 5K Planner")
    st.caption("A 5K-only planner that stays in percentage-based vocabulary.")

    if "history_rows" not in st.session_state:
        st.session_state["history_rows"] = _default_history_rows()

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

    if st.button("Generate Next Workout", type="primary", use_container_width=True):
        try:
            result = generate_next_workout(
                phase=phase,
                capacities=capacities,
                history=history_records,
                readiness=readiness,
            )
            _render_result(result)
            if pace_ladder is not None:
                st.markdown(
                    f"**Primary percent pace:** {pace_ladder[result.selected_percent]['pace_per_mile']}/mi"
                    f" | {pace_ladder[result.selected_percent]['pace_per_km']}/km"
                )
                if result.secondary_percents:
                    secondary_paces = ", ".join(
                        f"{format_percent(percent)} = {pace_ladder[percent]['pace_per_mile']}/mi"
                        f" ({pace_ladder[percent]['pace_per_km']}/km)"
                        for percent in result.secondary_percents
                    )
                    st.markdown(f"**Secondary percent paces:** {secondary_paces}")
        except ValueError as exc:
            st.error(str(exc))

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


if __name__ == "__main__":
    main()
