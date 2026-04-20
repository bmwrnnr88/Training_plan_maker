# Percentage-Based 5K Planner

This project is a percentage-based training planner for the 5K.

## Core rules

- Keep the planner language percentage-based.
- Workouts are described by:
  - primary percent
  - optional secondary percents
  - family
  - build direction
  - phase fit
  - equivalent volume
  - estimated work/rest time
  - load estimate
  - readiness and capacity gates
- The user chooses phase: `general`, `supportive`, or `specific`.
- The planner uses:
  - current capacity by percent rung
  - recent workout history
  - phase exposure quotas
  - load spacing
  - anti-regression logic
- For now, this system is **5K only**.

## Important design constraints

- Do **not** use physiological labels like threshold, CV, direct support, or specific speed endurance in the UI.
- Keep the core selection logic in percentage vocabulary.
- Do **not** regress an advanced athlete unnecessarily. If the athlete has already demonstrated a high-level workout at a percent, the planner should respect an anti-regression floor.
- When capacity is lower, prefer shorter reps and/or more segmented structures before longer, denser structures.
- Phase controls **what percentages are emphasized and how often**, not an artificial cap on what level the athlete is allowed to do.

## Target app behavior

The Streamlit app should let the user:

1. Choose phase.
2. Enter readiness (1-5).
3. Enter current capacity for 80, 85, 90, 95, 100, 105, 110, and 115.
4. Enter/edit recent workout history.
5. Click **Generate Next Workout**.

The app should output:

- selected primary percent
- secondary percents if any
- selected workout text
- estimated load
- load class
- a short reason summary

## Running

```bash
pip install -r requirements.txt
streamlit run app.py
```
