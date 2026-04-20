from __future__ import annotations

PEAK_EQUIVALENTS_5K = {
    80: 16093,   # 10 mi
    85: 8045,    # 5 mi
    90: 11265,   # 7 mi
    95: 9100,    # 35 min split 95%
    100: 7200,   # 6 x 1200
    105: 6000,   # 2 x (6 x 500)
    110: 3200,   # 16 x 200
    115: 800,    # 8 x 100m strides / fast relaxed sprints
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
