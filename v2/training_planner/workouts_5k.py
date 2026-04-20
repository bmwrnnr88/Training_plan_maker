from __future__ import annotations

from models import PercentWorkout

WORKOUTS_5K_95 = [
    PercentWorkout("5k_95_single_01", "5k", 95, [], "single_percent_continuous", "single_percent", "15 min at 95%", ["general"], 1, "low", 4000, 15.0, 0.0, 22.5, 0.35, 2, 1, False),
    PercentWorkout("5k_95_single_02", "5k", 95, [], "single_percent_continuous", "single_percent", "20 min split 95%", ["general"], 2, "low", 5200, 20.0, 0.0, 30.0, 0.45, 2, 2, False),
    PercentWorkout("5k_95_single_03", "5k", 95, [], "single_percent_continuous", "single_percent", "25 min split 95%", ["general", "supportive"], 3, "low", 6500, 25.0, 0.0, 37.5, 0.55, 3, 3, False),
    PercentWorkout("5k_95_single_04", "5k", 95, [], "single_percent_continuous", "single_percent", "30 min split 95%", ["general", "supportive"], 4, "low", 7800, 30.0, 0.0, 45.0, 0.65, 3, 4, True),
    PercentWorkout("5k_95_single_05", "5k", 95, [], "single_percent_continuous", "single_percent", "35 min split 95%", ["supportive"], 5, "low", 9100, 35.0, 0.0, 52.5, 0.80, 4, 5, True),
    PercentWorkout("5k_95_single_06", "5k", 95, [], "single_percent_intervals", "single_percent", "4 x 2k at 95% with 3 min jog", ["general", "supportive", "specific"], 5, "low", 8000, 30.0, 9.0, 47.25, 0.70, 3, 5, True),
]

WORKOUTS_5K_95_100_TOP_DOWN = [
    PercentWorkout("5k_95_100_td_01", "5k", 95, [100], "top_down", "top_down", "6 x 1 mile at 95% with 1-2 min rest", ["general", "supportive"], 5, "low", 9650, 36.0, 7.5, 55.9, 0.85, 4, 5, True),
    PercentWorkout("5k_95_100_td_02", "5k", 95, [100], "top_down", "top_down", "5 x 1 mile at 100% support pace with 2-3 min rest", ["supportive", "specific"], 4, "low", 8045, 30.0, 10.0, 41.5, 0.70, 3, 4, True),
    PercentWorkout("5k_95_100_td_03", "5k", 95, [100], "top_down", "top_down", "3 x 1 mile at 95%, then 2 x 1000m at 100% with 3 min rest", ["supportive", "specific"], 4, "medium", 6825, 26.0, 9.0, 39.9, 0.65, 3, 3, True),
    PercentWorkout("5k_95_100_td_04", "5k", 95, [100], "blend", "blend", "20 min at 95%, 5 min rest, 5 min at 100%", ["supportive"], 3, "low", 6500, 25.0, 5.0, 38.75, 0.55, 3, 2, False),
]

WORKOUTS_5K_100_BOTTOM_UP = [
    PercentWorkout("5k_100_bu_01", "5k", 100, [], "bottom_up", "bottom_up", "3 x (4 x 400m) at 100% with 30 sec rest, 5 min between sets", ["general", "supportive"], 2, "medium", 4800, 17.0, 13.0, 32.1, 0.45, 2, 1, False),
    PercentWorkout("5k_100_bu_02", "5k", 100, [], "bottom_up", "bottom_up", "3 x (3 x 600m) at 100% with 40 sec rest, 5 min between sets", ["general", "supportive"], 3, "medium", 5400, 19.0, 12.0, 35.3, 0.55, 3, 2, False),
    PercentWorkout("5k_100_bu_03", "5k", 100, [], "bottom_up", "bottom_up", "2 x (3 x 800m) at 100% with 45 sec rest, 5 min between sets", ["supportive"], 4, "medium", 4800, 17.5, 9.5, 32.1, 0.60, 3, 3, False),
    PercentWorkout("5k_100_bu_04", "5k", 100, [], "single_percent_intervals", "single_percent", "5 x 1000m at 100% with 60-75 sec rest", ["specific"], 4, "medium", 5000, 18.0, 5.5, 31.9, 0.70, 3, 4, True),
    PercentWorkout("5k_100_bu_05", "5k", 100, [], "single_percent_intervals", "single_percent", "6 x 1200m at 100% with 3 min jog", ["specific"], 5, "medium", 7200, 26.0, 15.0, 47.95, 0.90, 4, 5, True),
]

WORKOUTS_5K_100_85_ALTERNATIONS = [
    PercentWorkout("5k_100_85_alt_01", "5k", 100, [85], "alternation", "alternation", "4 miles alternating 200m at 100% with 1400m at 85%", ["general", "supportive"], 2, "low", 6437, 29.0, 0.0, 29.0, 0.45, 2, 1, False),
    PercentWorkout("5k_100_85_alt_02", "5k", 100, [85], "alternation", "alternation", "4 miles alternating 400m at 100% with 1200m at 85%", ["general", "supportive"], 3, "low", 6437, 29.5, 0.0, 31.8, 0.55, 2, 2, False),
    PercentWorkout("5k_100_85_alt_03", "5k", 100, [85], "alternation", "alternation", "4 miles alternating 600m at 100% with 1000m at 85%", ["supportive"], 4, "low", 6437, 30.0, 0.0, 34.7, 0.65, 3, 3, False),
    PercentWorkout("5k_100_85_alt_04", "5k", 100, [85], "alternation", "alternation", "4 miles alternating 800m at 100% with 800m at 85%", ["supportive", "specific"], 5, "medium", 6437, 30.5, 0.0, 37.5, 0.75, 3, 4, True),
]

WORKOUTS_5K_100_105 = [
    PercentWorkout("5k_100_105_blend_01", "5k", 100, [105], "blend", "blend", "3 x (1200m at 100%, 1 min rest, 400m at 105%), 5 min between sets", ["specific"], 4, "high", 4800, 18.0, 12.0, 34.5, 0.70, 3, 1, False),
    PercentWorkout("5k_100_105_blend_02", "5k", 100, [105], "combo", "combo", "4 x 5 min at 95-100% support pace with 3 min rest, 5 min rest, then 4 x 60 sec at 100-105%", ["supportive"], 4, "medium", 6500, 24.0, 14.0, 37.0, 0.60, 3, 2, False),
]

WORKOUTS_5K_105 = [
    PercentWorkout("5k_105_single_01", "5k", 105, [], "single_percent_intervals", "single_percent", "6 x 500m at 105% with 45 sec rest", ["general", "supportive"], 2, "medium", 3000, 10.5, 3.75, 20.9, 0.40, 2, 1, False),
    PercentWorkout("5k_105_single_02", "5k", 105, [], "single_percent_intervals", "single_percent", "8 x 500m at 105% with 45 sec rest", ["supportive"], 3, "medium", 4000, 14.0, 5.25, 27.9, 0.55, 3, 2, False),
    PercentWorkout("5k_105_single_03", "5k", 105, [], "single_percent_intervals", "single_percent", "6 x 600m at 105% with 60 sec rest", ["supportive"], 3, "medium", 3600, 12.5, 5.0, 25.0, 0.55, 3, 3, False),
    PercentWorkout("5k_105_single_04", "5k", 105, [], "single_percent_intervals", "single_percent", "2 x (6 x 500m) at 105% with 45 sec rest, 5 min between sets", ["specific"], 5, "medium", 6000, 21.0, 13.25, 43.2, 0.90, 4, 5, True),
]

WORKOUTS_5K_110_115 = [
    PercentWorkout("5k_110_single_01", "5k", 110, [], "single_percent_intervals", "single_percent", "10 x 200m at 110% with 60 sec jog", ["supportive", "specific"], 2, "high", 2000, 6.5, 10.0, 16.8, 0.45, 3, 1, False),
    PercentWorkout("5k_110_single_02", "5k", 110, [], "single_percent_intervals", "single_percent", "16 x 200m at 110% with 60 sec jog", ["supportive", "specific"], 5, "high", 3200, 10.5, 16.0, 27.1, 0.90, 4, 5, True),
    PercentWorkout("5k_115_single_01", "5k", 115, [], "maintenance", "maintenance", "6 x 8 sec hill sprints", ["general", "supportive", "specific"], 1, "medium", 300, 0.8, 4.0, 3.0, 0.20, 2, 1, False),
    PercentWorkout("5k_115_single_02", "5k", 115, [], "maintenance", "maintenance", "8 x 100m strides / fast relaxed sprints", ["general", "supportive", "specific"], 2, "high", 800, 1.8, 8.0, 6.5, 0.30, 2, 2, False),
]

WORKOUTS_5K_SUPPORT = [
    PercentWorkout("5k_80_single_01", "5k", 80, [], "single_percent_continuous", "single_percent", "8 miles at 80%", ["general"], 1, "low", 12875, 58.0, 0.0, 40.6, 0.40, 2, 1, False),
    PercentWorkout("5k_80_single_02", "5k", 80, [], "single_percent_continuous", "single_percent", "10 miles at 80%", ["general", "supportive"], 3, "low", 16093, 72.0, 0.0, 50.4, 0.55, 3, 2, True),
    PercentWorkout("5k_85_single_01", "5k", 85, [], "single_percent_continuous", "single_percent", "5 miles at 85%", ["general", "supportive"], 2, "low", 8045, 33.0, 0.0, 29.7, 0.45, 2, 1, False),
    PercentWorkout("5k_90_single_01", "5k", 90, [], "single_percent_continuous", "single_percent", "4 miles at 90%", ["general", "supportive", "specific"], 2, "low", 6437, 24.5, 0.0, 24.5, 0.40, 2, 1, False),
    PercentWorkout("5k_90_single_02", "5k", 90, [], "single_percent_continuous", "single_percent", "7 miles at 90%", ["supportive", "specific"], 5, "low", 11265, 43.0, 0.0, 43.0, 0.80, 3, 2, True),
]

WORKOUT_DB_5K = (
    WORKOUTS_5K_95
    + WORKOUTS_5K_95_100_TOP_DOWN
    + WORKOUTS_5K_100_BOTTOM_UP
    + WORKOUTS_5K_100_85_ALTERNATIONS
    + WORKOUTS_5K_100_105
    + WORKOUTS_5K_105
    + WORKOUTS_5K_110_115
    + WORKOUTS_5K_SUPPORT
)
