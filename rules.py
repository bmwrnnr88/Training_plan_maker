from __future__ import annotations

from typing import List, Tuple


DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

PHASE_NAMES = {
    "general": "General Phase",
    "supportive": "Race-Supportive Phase",
    "specific": "Race-Specific Phase",
}

EVENT_CATEGORY = {
    "800m": "middle_distance",
    "1500m": "middle_distance",
    "mile": "middle_distance",
    "3k": "distance",
    "5k": "distance",
    "10k": "distance",
    "half_marathon": "long_distance",
    "marathon": "marathon",
}


def choose_phase_lengths(
    weeks_to_race: int,
    experience: str,
    max_mileage: int,
) -> List[str]:
    if weeks_to_race < 6:
        raise ValueError("Need at least 6 weeks.")

    if experience == "novice" or max_mileage < 40:
        specific = 4
        supportive = 2 if weeks_to_race <= 8 else 3
    elif experience == "advanced" and max_mileage >= 60:
        specific = min(6, max(4, weeks_to_race // 3))
        supportive = min(4, max(2, weeks_to_race // 4))
    else:
        specific = min(5, max(4, weeks_to_race // 3))
        supportive = min(4, max(3, weeks_to_race // 4))

    general = weeks_to_race - specific - supportive
    if general < 1:
        general = 1
        supportive = max(1, weeks_to_race - specific - general)

    phases = (["general"] * general) + (["supportive"] * supportive) + (["specific"] * specific)
    return phases[:weeks_to_race]


def weekly_mileage_targets(
    current_mileage: int,
    max_mileage: int,
    weeks_to_race: int,
    phases: List[str],
) -> List[int]:
    peak = max(current_mileage, max_mileage)
    targets: List[int] = []

    for i, phase in enumerate(phases):
        week_num = i + 1

        if phase == "general":
            frac = week_num / max(1, phases.count("general"))
            mileage = round(current_mileage + (peak - current_mileage) * 0.75 * frac)
        elif phase == "supportive":
            mileage = round(current_mileage + 0.8 * (peak - current_mileage))
            mileage = min(mileage + 2, peak)
        else:
            taper_factor = 1.0
            remaining_specific = phases[i:].count("specific")
            if remaining_specific <= 2:
                taper_factor = 0.88
            elif remaining_specific == 3:
                taper_factor = 0.95
            mileage = round(peak * taper_factor)

        targets.append(max(10, mileage))

    return targets


def hard_day_spacing(days_per_week: int, day_off: str) -> Tuple[str, str]:
    if days_per_week <= 4:
        return "Tuesday", "Saturday"
    if day_off == "Sunday":
        return "Tuesday", "Friday"
    return "Tuesday", "Saturday"


def phase_notes(phase: str) -> List[str]:
    if phase == "general":
        return [
            "General phase emphasizes aerobic development and low-key exposure to relevant paces.",
            "Endurance is emphasized more often than speed.",
        ]
    if phase == "supportive":
        return [
            "Race-supportive phase increases 90% and 110% work as stepping stones toward 95/100/105.",
            "Specificity rises, but the plan still keeps general support in place.",
        ]
    return [
        "Race-specific phase centers on 95%, 100%, and 105% work.",
        "Mileage matters less here than freshness for key sessions.",
    ]
