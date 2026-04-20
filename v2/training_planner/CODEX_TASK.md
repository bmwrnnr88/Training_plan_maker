# Codex task: build the remaining files for the percentage-based 5K planner

You are continuing an existing project scaffold.

Read these files first:
- README.md
- models.py
- config.py
- workouts_5k.py

## Non-negotiable rules

1. Keep everything in **percentage-based vocabulary**.
2. In the UI and core planner logic, do **not** use physiological labels like threshold, CV, direct support, or specific speed endurance.
3. Workouts must be selected using:
   - primary_percent
   - secondary_percents
   - family
   - build_direction
   - phase_fit
   - difficulty_rank
   - equivalent_volume_m
   - estimated_work_minutes
   - estimated_rest_minutes
   - load_estimate
   - minimum_capacity
   - minimum_readiness
   - progression_order
   - anti_regression_floor
4. This app is **5K only** for now.
5. The user chooses phase: `general`, `supportive`, or `specific`.
6. The planner must consider:
   - current capacity by percent rung
   - recent history from the last 14-21 days
   - phase quotas by percent
   - load-based spacing
   - anti-regression floor based on recent best work
7. If the athlete has already demonstrated a high-level workout at a percent, do not regress them unnecessarily.
8. When capacity is lower, prefer shorter reps / more segmented versions before longer, denser versions.

## Files that already exist

- models.py
- config.py
- workouts_5k.py

## Files you need to create

### 1. requirements.txt
Include the minimum needed to run the app:
- streamlit>=1.35
- pandas>=2.0

### 2. load_model.py
Implement:

```python
from typing import Dict

def compute_load(minutes_by_percent: Dict[int, float], rest_minutes: float) -> float:
    ...

def classify_load(load_score: float) -> str:
    ...
```

Rules:
- Use LOAD_WEIGHTS from config.py
- Add rest using LOAD_WEIGHTS["rest"]
- Load classes:
  - <20 easy
  - 20-35 moderate
  - 35-50 hard
  - >50 very_hard

### 3. capacity.py
Implement:

```python
from typing import Optional

def normalize_capacity(percent: int, completed_equivalent_m: int) -> float:
    ...

def target_equivalent_from_capacity(
    percent: int,
    capacity: float,
    recent_best_equivalent_m: Optional[int],
    experience_floor: float = 0.9,
) -> int:
    ...
```

Rules:
- normalize against PEAK_EQUIVALENTS_5K
- anti-regression rule:
  `target = max(peak * capacity, recent_best * experience_floor)`
- clamp outputs sensibly so they never exceed the peak by default

### 4. history.py
Implement a simple history layer.

Use SessionRecord from models.py.

Implement:

```python
from typing import Iterable, List, Optional


def get_recent_sessions(history: Iterable[SessionRecord], days: int) -> List[SessionRecord]:
    ...


def count_percent_exposures(history: Iterable[SessionRecord], percent: int, window_days: int) -> int:
    ...


def days_since_percent(history: Iterable[SessionRecord], percent: int) -> Optional[int]:
    ...


def recent_best_equivalent(history: Iterable[SessionRecord], percent: int, window_days: int = 42) -> Optional[int]:
    ...
```

Rules:
- A workout counts as exposure if the percent appears as primary or in secondary_percents.
- Use the current date from the machine for day calculations.
- Be robust to empty history.

### 5. utils.py
Implement helpers for:
- formatting percents as strings
- formatting secondary percents
- sorting workouts by progression_order, difficulty_rank, and equivalent_volume_m
- simple helper to convert a capacity dict into a readable table if useful

### 6. selector.py
Implement the percent selector.

Main function:

```python
from typing import Dict, Iterable
from models import SessionRecord, Phase


def select_candidate_percent(
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> tuple[int, str]:
    ...
```

Return:
- selected primary percent
- short reason summary

Scoring factors:
1. phase quota deficit
2. recency bonus/penalty
3. capacity weakness
4. readiness gate
5. recent load spacing

Required behavior:
- General phase should emphasize 80/85/90/95 and only lightly touch 100/105.
- Supportive phase should emphasize 90/95/100/105.
- Specific phase should emphasize 95/100/105 with maintenance of 90 and 110/115.
- If readiness is too low, do not select a high-demand percent unless all signals strongly force it.
- If recent history shows too much recent load, block or penalize higher-stress options.

Suggested logic:
- quota deficit should matter the most
- recency should matter next
- weakness by capacity should matter next
- readiness and recent load should work mainly as gates/penalties

### 7. planner.py
Implement the workout selector.

Main function:

```python
from typing import Dict, Iterable
from models import Phase, SessionRecord, PlannerResult


def select_workout_template(
    percent: int,
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> PlannerResult:
    ...
```

Rules:
- Pull candidates from WORKOUT_DB_5K.
- Filter by:
  - matching primary_percent
  - phase_fit
  - minimum_capacity
  - minimum_readiness
- Respect anti-regression floor using recent_best_equivalent.
- Prefer appropriate progression_order for the athlete instead of always choosing the biggest workout.
- If the athlete is more advanced at that percent, do not downshift into beginner templates unless readiness/load clearly require it.
- Output:
  - selected_percent
  - selected_workout_id
  - workout_text
  - secondary_percents
  - load_estimate
  - load_class
  - reason_summary

Also implement a wrapper:

```python
def generate_next_workout(
    phase: Phase,
    capacities: Dict[int, float],
    history: Iterable[SessionRecord],
    readiness: int,
) -> PlannerResult:
    ...
```

This should:
1. call select_candidate_percent
2. call select_workout_template
3. return the result

### 8. app.py
Build a clean Streamlit UI.

Required sections:
1. Phase selector
2. Readiness selector (1-5)
3. Capacity inputs for 80, 85, 90, 95, 100, 105, 110, 115
4. Recent history editor
5. Generate Next Workout button

Display requirements:
- Show selected percent clearly, e.g. `Primary percent: 100%`
- Show secondary percents, e.g. `Secondary percents: 85%`
- Show workout text
- Show load estimate and load class
- Show reason summary

History editor requirements:
- Keep it simple and local to the app state
- Let the user add rows with:
  - date
  - primary percent
  - secondary percents (comma-separated)
  - workout text
  - equivalent volume
  - load score
  - load class
  - mechanical flag

### 9. tests_optional.py
If helpful, add a small manual test script with a sample capacity dict and a few sessions in history.
This is optional but useful.

## Style requirements

- Use type hints.
- Use docstrings.
- Keep the code modular.
- Make it runnable with `streamlit run app.py`.
- Do not radically change the existing file architecture.
- Do not rename the existing dataclass fields.

## Important final constraint

The planner should feel like a **percentage-based coach**, not a generic training app.
