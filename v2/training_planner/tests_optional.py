from __future__ import annotations

from pprint import pprint

from models import SessionRecord
from planner import generate_next_workout


def main() -> None:
    capacities = {
        80: 0.7,
        85: 0.6,
        90: 0.65,
        95: 0.55,
        100: 0.5,
        105: 0.45,
        110: 0.35,
        115: 0.3,
    }

    history = [
        SessionRecord(
            date="2026-04-12",
            primary_percent=90,
            secondary_percents=[],
            workout_text="4 miles at 90%",
            equivalent_volume_m=6437,
            load_score=24.5,
            load_class="moderate",
            mechanical_flag="low",
        ),
        SessionRecord(
            date="2026-04-15",
            primary_percent=100,
            secondary_percents=[85],
            workout_text="4 miles alternating 400m at 100% with 1200m at 85%",
            equivalent_volume_m=6437,
            load_score=31.8,
            load_class="moderate",
            mechanical_flag="low",
        ),
    ]

    result = generate_next_workout(
        phase="supportive",
        capacities=capacities,
        history=history,
        readiness=3,
    )
    pprint(result)


if __name__ == "__main__":
    main()
