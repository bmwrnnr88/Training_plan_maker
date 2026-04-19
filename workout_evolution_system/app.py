from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workout_evolution_system.pace_ladder import PACE_BANDS, build_fixed_pace_ladder
from workout_evolution_system.progression import (
    describe_workout,
    next_progression_for_band,
    progress_ratio_for_band,
    workout_volume_miles,
)
from workout_evolution_system.state import default_workout_states, rows_to_states, states_to_rows
from workout_evolution_system.weekly_planner import generate_weekly_plan


PROFILE_PATH = Path(__file__).with_name("athlete_profile.json")


def _load_profile() -> dict[str, str]:
    return json.loads(PROFILE_PATH.read_text())


def _pace_ladder_df(ladder: dict[int, dict[str, float | str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Band": f"{band}%",
                "Zone": ladder[band]["zone"],
                "Pace / mile": ladder[band]["pace_per_mile"],
                "Pace / km": ladder[band]["pace_per_km"],
            }
            for band in reversed(PACE_BANDS)
        ]
    )


def _progressions_df(states: dict[int, dict[str, object]], ladder: dict[int, dict[str, float | str]]) -> pd.DataFrame:
    rows = []
    for band in PACE_BANDS:
        next_step = next_progression_for_band(states[band], ladder)
        rows.append(
            {
                "Band": f"{band}%",
                "Zone": states[band]["zone"],
                "Current": describe_workout(states[band], ladder),
                "Next suggestion": describe_workout(next_step["state"], ladder),
                "Progress": f"{progress_ratio_for_band(states[band]) * 100:.0f}%",
                "Reason": next_step["reason"],
            }
        )
    return pd.DataFrame(rows)


st.set_page_config(page_title="Workout Evolution System", layout="wide")

st.title("Workout Evolution Running System")
st.write(
    "Fixed paces come from the baseline 5k once, then workouts evolve by volume, density, and continuity."
)

profile = _load_profile()

with st.sidebar:
    st.header("Baseline Fitness")
    mile_time = st.text_input("Mile", value=profile["mile"])
    two_mile_time = st.text_input("Two mile", value=profile["two_mile"])
    five_k_time = st.text_input("5K", value=profile["5k"])
    ten_k_time = st.text_input("10K", value=profile["10k"])
    half_time = st.text_input("Half", value=profile["half"])

    st.caption("Only the 5K mark sets the pace ladder. The other marks stay as reference context.")

    phase = st.selectbox(
        "Current phase",
        ["general", "race-supportive", "race-specific"],
        index=0,
    )

    limiter_choice = st.selectbox(
        "Limiter",
        ["auto", "endurance", "cv", "speed"],
        index=0,
    )

    if st.button("Reset workout state"):
        st.session_state.pop("we_state_rows", None)
        st.session_state.pop("we_baseline_5k", None)

athlete_profile = {
    "mile": mile_time,
    "two_mile": two_mile_time,
    "5k": five_k_time,
    "10k": ten_k_time,
    "half": half_time,
}

try:
    ladder = build_fixed_pace_ladder(athlete_profile)
except ValueError as exc:
    st.error(f"Could not build the fixed pace ladder: {exc}")
    st.stop()

default_states = default_workout_states(ladder)
default_rows = states_to_rows(default_states)

if (
    "we_state_rows" not in st.session_state
    or st.session_state.get("we_baseline_5k") != athlete_profile["5k"]
):
    st.session_state["we_state_rows"] = default_rows
    st.session_state["we_baseline_5k"] = athlete_profile["5k"]

st.subheader("Fixed Pace Ladder")
st.dataframe(_pace_ladder_df(ladder), width="stretch", hide_index=True)

st.subheader("Editable Workout State")
edited_df = st.data_editor(
    pd.DataFrame(st.session_state["we_state_rows"]),
    hide_index=True,
    width="stretch",
    column_config={
        "band": st.column_config.NumberColumn("Band", disabled=True),
        "zone": st.column_config.TextColumn("Zone", disabled=True),
        "pace_per_mile": st.column_config.TextColumn("Pace / mile", disabled=True),
        "workout_type": st.column_config.SelectboxColumn(
            "Workout type",
            options=["continuous", "interval", "broken_tempo"],
            required=True,
        ),
        "reps": st.column_config.NumberColumn("Reps", min_value=0, step=1),
        "distance_m": st.column_config.NumberColumn("Rep distance (m)", min_value=0, step=100),
        "distance_miles": st.column_config.NumberColumn("Distance (mi)", min_value=0.0, step=0.5),
        "rest_sec": st.column_config.NumberColumn("Rest (sec)", min_value=0, step=15),
        "target": st.column_config.TextColumn("Target", width="large"),
    },
)

states = rows_to_states(edited_df.to_dict("records"), ladder)
st.session_state["we_state_rows"] = states_to_rows(states)

st.subheader("Progression Suggestions")
st.dataframe(_progressions_df(states, ladder), width="stretch", hide_index=True)

st.subheader("Weekly Plan Output")
weekly_plan = generate_weekly_plan(
    states=states,
    ladder=ladder,
    phase=phase,
    limiter=None if limiter_choice == "auto" else limiter_choice,
)

metric_columns = st.columns(4)
metric_columns[0].metric("Primary band", f"{weekly_plan['primary_band']}%")
metric_columns[1].metric("Support band", f"{weekly_plan['support_band']}%")
metric_columns[2].metric(
    "Peak aerobic work",
    f"{weekly_plan['peak_metrics']['peak_aerobic_work']:.1f} mi",
)
metric_columns[3].metric(
    "Weekly target",
    f"{weekly_plan['weekly_target_miles']:.1f} mi",
)

st.write(
    f"Long run recommendation: {weekly_plan['long_run']['recommended']:.1f} mi "
    f"(range {weekly_plan['long_run']['minimum']:.1f}-{weekly_plan['long_run']['maximum']:.1f})."
)

schedule_df = pd.DataFrame(weekly_plan["schedule"])
st.dataframe(schedule_df, width="stretch", hide_index=True)

st.write("PeakAerobicWork components")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Threshold work": f"{weekly_plan['peak_metrics']['threshold_work']:.1f} mi",
                "Race-pace work": f"{weekly_plan['peak_metrics']['race_work']:.1f} mi",
                "Longest steady run": f"{weekly_plan['peak_metrics']['steady_run']:.1f} mi",
                "Driver": weekly_plan["peak_metrics"]["driver"],
            }
        ]
    ),
    width="stretch",
    hide_index=True,
)

st.write("Planner notes")
for note in weekly_plan["notes"]:
    st.write(f"- {note}")

st.write("Current workout volume by band")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Band": f"{band}%",
                "Workout volume": f"{workout_volume_miles(states[band]):.1f} mi",
            }
            for band in PACE_BANDS
        ]
    ),
    width="stretch",
    hide_index=True,
)
