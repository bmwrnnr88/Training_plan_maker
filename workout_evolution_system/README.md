# Workout Evolution System

This directory contains a separate running-training system built around:

1. Fixed pace ladders from baseline 5k fitness
2. Workout evolution over time
3. Weekly planning from current workout state

Key constraints in this version:

- Paces are initialized once from the 5k and never auto-updated
- Workouts evolve by volume, density, and continuity
- No anchor-race logic
- No race-distance scaling for workout duration

Run the Streamlit UI with:

```bash
streamlit run workout_evolution_system/app.py
```
