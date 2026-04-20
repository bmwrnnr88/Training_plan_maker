from __future__ import annotations

PEAK_EQUIVALENTS_5K = {
    80: 24140,   # 15 mi
    85: 14484,   # 9 mi
    90: 11265,   # 7 mi
    95: 8000,    # 4 x 2 km at 95%
    100: 7200,   # 6 x 1200
    105: 6000,   # 2 x (6 x 500)
    110: 3200,   # 16 x 200
    115: 2400,   # 12 x 200
}

ARTICLE_PEAK_TARGETS_5K = {
    80: [
        {"style": "Peak target", "workout_text": "8-15 miles at 80%", "equivalent_volume_m": 24140},
    ],
    85: [
        {"style": "Peak target", "workout_text": "5-9 miles at 85%", "equivalent_volume_m": 14484},
    ],
    90: [
        {"style": "Peak target", "workout_text": "4-7 miles at 90%", "equivalent_volume_m": 11265},
    ],
    95: [
        {"style": "Peak target", "workout_text": "4 x 2 km at 95% with 3 min jog", "equivalent_volume_m": 8000},
        {"style": "Peak target", "workout_text": "4-6 km continuous at 95%", "equivalent_volume_m": 6000},
    ],
    100: [
        {"style": "Peak target", "workout_text": "5-6 x 1200m at 100% with 3 min jog", "equivalent_volume_m": 7200},
    ],
    105: [
        {
            "style": "Peak target",
            "workout_text": "2 sets of (5-6 x 500m at 105%) with 45 sec and 4-5 min recovery",
            "equivalent_volume_m": 6000,
        },
    ],
    110: [
        {"style": "Peak target", "workout_text": "16 x 200m at 110% with 1-2 min jog", "equivalent_volume_m": 3200},
    ],
    115: [
        {"style": "Peak target", "workout_text": "10-12 x 200m at 115% with 2-3 min walk/jog", "equivalent_volume_m": 2400},
    ],
}

PHASE_QUOTAS_5K = {
    "general": {
        80: {"window_days": 14, "target_min": 2, "target_max": 4},
        85: {"window_days": 21, "target_min": 1, "target_max": 1},
        90: {"window_days": 14, "target_min": 1, "target_max": 2},
        95: {"window_days": 10, "target_min": 1, "target_max": 1},
        100: {"window_days": 14, "target_min": 0, "target_max": 1},
        105: {"window_days": 14, "target_min": 0, "target_max": 1},
        110: {"window_days": 21, "target_min": 0, "target_max": 1},
        115: {"window_days": 7, "target_min": 1, "target_max": 2},
    },
    "supportive": {
        80: {"window_days": 14, "target_min": 2, "target_max": 3},
        85: {"window_days": 21, "target_min": 1, "target_max": 1},
        90: {"window_days": 14, "target_min": 2, "target_max": 2},
        95: {"window_days": 10, "target_min": 1, "target_max": 1},
        100: {"window_days": 14, "target_min": 1, "target_max": 1},
        105: {"window_days": 14, "target_min": 1, "target_max": 1},
        110: {"window_days": 14, "target_min": 1, "target_max": 1},
        115: {"window_days": 10, "target_min": 1, "target_max": 1},
    },
    "specific": {
        80: {"window_days": 14, "target_min": 1, "target_max": 2},
        85: {"window_days": 21, "target_min": 0, "target_max": 1},
        90: {"window_days": 10, "target_min": 1, "target_max": 1},
        95: {"window_days": 14, "target_min": 1, "target_max": 2},
        100: {"window_days": 14, "target_min": 1, "target_max": 2},
        105: {"window_days": 10, "target_min": 1, "target_max": 1},
        110: {"window_days": 21, "target_min": 0, "target_max": 1},
        115: {"window_days": 14, "target_min": 1, "target_max": 1},
    },
}

LOAD_WEIGHTS = {
    "very_easy": 0.25,
    "easy": 0.40,
    80: 0.70,
    85: 0.90,
    90: 1.00,
    95: 1.50,
    100: 1.70,
    105: 1.90,
    110: 2.20,
    115: 2.50,
    "rest": 0.25,
}

LOAD_THRESHOLDS = {
    "easy_max": 20.0,
    "moderate_max": 35.0,
    "hard_max": 50.0,
}

READINESS_MIN = 1
READINESS_MAX = 5
DEFAULT_EXPERIENCE_FLOOR = 0.90
DEFAULT_HISTORY_WINDOW_DAYS = 21
RECENCY_PENALTIES = {
    "0_2": -2,
    "3_5": -1,
    "6_9": 1,
    "10_plus": 2,
}
