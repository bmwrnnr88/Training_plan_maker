from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

Phase = Literal["general", "supportive", "specific"]
BuildDirection = Literal[
    "single_percent",
    "top_down",
    "bottom_up",
    "alternation",
    "blend",
    "combo",
    "maintenance",
    "special_block",
]
MechanicalFlag = Literal["low", "medium", "high"]
LoadClass = Literal["easy", "moderate", "hard", "very_hard"]
ScheduleStatus = Literal["planned", "completed", "partial", "missed"]
ScheduleType = Literal["quality", "support", "long_support", "recovery", "easy", "off"]


@dataclass(frozen=True)
class PercentWorkout:
    id: str
    event: str
    primary_percent: int
    secondary_percents: List[int]
    family: str
    build_direction: BuildDirection
    workout_text: str
    phase_fit: List[Phase]
    difficulty_rank: int
    mechanical_flag: MechanicalFlag
    equivalent_volume_m: int
    estimated_work_minutes: float
    estimated_rest_minutes: float
    load_estimate: float
    minimum_capacity: float
    minimum_readiness: int
    progression_order: int
    anti_regression_floor: bool


@dataclass
class SessionRecord:
    date: str
    primary_percent: int
    secondary_percents: List[int]
    workout_text: str
    equivalent_volume_m: int
    load_score: float
    load_class: LoadClass
    mechanical_flag: MechanicalFlag


@dataclass
class PlannerResult:
    selected_percent: int
    selected_workout_id: str
    workout_text: str
    secondary_percents: List[int]
    load_estimate: float
    load_class: LoadClass
    reason_summary: str
    notes: Optional[str] = None


@dataclass
class ScheduleEntry:
    date: str
    day_label: str
    session_type: ScheduleType
    primary_percent: Optional[int]
    secondary_percents: List[int]
    workout_text: str
    equivalent_volume_m: int
    load_estimate: float
    load_class: LoadClass
    reason_summary: str
    status: ScheduleStatus = "planned"
    completion_ratio: float = 1.0
