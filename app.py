
import streamlit as st
from planner import AthleteProfile, GoalProfile, build_training_plan

st.set_page_config(page_title="Full-Spectrum Running Planner", layout="wide")

st.title("Full-Spectrum Running Plan Generator")
st.write(
    "Builds race plans using a percentage-based framework inspired by the Running Writings resources."
)

with st.sidebar:
    st.header("Athlete Profile")

    race_distance = st.selectbox(
        "Target race distance",
        ["800m", "1500m", "mile", "3k", "5k", "10k", "half_marathon", "marathon"],
        index=4,
    )

    current_distance = st.selectbox(
        "Distance of your current best / recent mark",
        ["800m", "1500m", "mile", "3k", "5k", "10k", "half_marathon", "marathon"],
        index=4,
    )

    current_time = st.text_input("Current time (mm:ss or hh:mm:ss)", value="17:50")

    weeks_to_race = st.slider("Weeks to race", min_value=6, max_value=24, value=12)
    current_mileage = st.slider("Current weekly mileage", min_value=15, max_value=100, value=40)
    max_mileage = st.slider("Maximum realistic weekly mileage", min_value=20, max_value=120, value=55)
    days_per_week = st.slider("Days per week", min_value=3, max_value=7, value=6)
    long_run_max = st.slider("Longest run you want in the plan (miles)", min_value=6, max_value=24, value=12)

    day_off = st.selectbox(
        "Preferred day off",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        index=6,
    )

    runner_type = st.selectbox(
        "Runner type",
        ["balanced", "endurance_oriented", "speed_oriented"],
        index=0,
    )

    experience = st.selectbox(
        "Experience level",
        ["novice", "intermediate", "advanced"],
        index=1,
    )

    doubles = st.checkbox("Allow doubles", value=False)
    track_access = st.checkbox("Track access", value=True)
    treadmill_access = st.checkbox("Treadmill access", value=True)

    build_clicked = st.button("Build plan", type="primary")

if build_clicked:
    athlete = AthleteProfile(
        current_distance=current_distance,
        current_time=current_time,
        current_mileage=current_mileage,
        max_mileage=max_mileage,
        days_per_week=days_per_week,
        long_run_max=long_run_max,
        day_off=day_off,
        runner_type=runner_type,
        experience=experience,
        doubles=doubles,
        track_access=track_access,
        treadmill_access=treadmill_access,
    )

    goal = GoalProfile(
        race_distance=race_distance,
        weeks_to_race=weeks_to_race,
    )

    plan = build_training_plan(athlete, goal)

    st.subheader("Plan Summary")
    st.write(f"**Target race:** {plan['summary']['race_distance']}")
    st.write(f"**Current fitness anchor:** {plan['summary']['fitness_anchor']}")
    st.write(f"**Phase structure:** {plan['summary']['phase_structure']}")
    st.write(f"**Peak mileage:** {plan['summary']['peak_mileage']} mi/week")

    st.subheader("Pace Table")
    st.dataframe(plan["paces_df"], use_container_width=True)

    st.subheader("Planning Notes")
    for note in plan["notes"]:
        st.write(f"- {note}")

    st.subheader("Weekly Plan")
    for week in plan["weeks"]:
        with st.expander(f"Week {week['week_number']} — {week['phase']} ({week['target_mileage']} mi)"):
            for day in week["days"]:
                st.write(f"**{day['day']}**: {day['session']}")
            st.write("**Why this week looks like this:**")
            for note in week["notes"]:
                st.write(f"- {note}")
else:
    st.info("Set your inputs in the sidebar, then click **Build plan**.")
