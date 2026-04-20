from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from datetime import date, timedelta
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import PEAK_EQUIVALENTS_5K
from load_model import classify_load, compute_load
from paces import PACE_BANDS, get_percentage_paces

RUN_TYPES = {"run", "trailrun", "treadmillrun"}
KEYWORD_PERCENT_HINTS = [
    (115, ("stride", "strides", "hill sprint", "sprint", "fast relaxed")),
    (110, ("200m", "200 m", "200@", "200 @")),
    (105, ("500m", "500 m", "600m", "600 m")),
    (100, ("1000m", "1000 m", "1k", "1200m", "1200 m")),
    (95, ("2k", "2000m", "2000 m", "split 95", "continuous 95")),
]


@dataclass(frozen=True)
class IntervalsImportResult:
    imported_rows: List[Dict[str, object]]
    scanned_entries: int
    candidate_activities: int
    skipped_note_entries: int
    skipped_non_runs: int
    skipped_missing_fields: int


def _basic_auth_header(api_key: str) -> str:
    credentials = base64.b64encode(f"API_KEY:{api_key}".encode("utf-8")).decode("utf-8")
    return f"Basic {credentials}"


def _request_json(url: str, api_key: str) -> object:
    request = Request(
        url,
        headers={
            "Authorization": _basic_auth_header(api_key),
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore") if exc.fp is not None else ""
        raise ValueError(f"Intervals.icu request failed ({exc.code}): {message or exc.reason}") from exc
    except URLError as exc:
        raise ValueError(f"Could not reach Intervals.icu: {exc.reason}") from exc


def fetch_recent_activities(
    api_key: str,
    athlete_id: int = 0,
    days: int = 21,
) -> List[dict]:
    """Fetch recent activity summaries from Intervals.icu."""
    newest = date.today()
    oldest = newest - timedelta(days=max(days, 1))
    query = urlencode({"oldest": oldest.isoformat(), "newest": newest.isoformat()})
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/activities?{query}"
    return list(_request_json(url, api_key))


def fetch_activity_detail(api_key: str, activity_id: str) -> dict:
    """Fetch one activity document for a concrete Intervals.icu activity id."""
    url = f"https://intervals.icu/api/v1/activity/{activity_id}"
    return dict(_request_json(url, api_key))


def _is_run_activity(activity: dict) -> bool:
    activity_type = str(activity.get("type", "")).replace(" ", "").lower()
    return activity_type in RUN_TYPES


def _looks_like_completed_activity(activity: dict) -> bool:
    activity_id = str(activity.get("id", "")).strip()
    if not activity_id:
        return False
    if "_note" in activity:
        return False
    if activity_id.startswith("i"):
        return True
    activity_type = str(activity.get("type", "")).strip()
    return bool(activity_type)


def _needs_detail(activity: dict) -> bool:
    if not str(activity.get("id", "")).startswith("i"):
        return False
    return any(
        activity.get(key) in (None, "")
        for key in ("type", "distance", "moving_time")
    )


def _activity_date(activity: dict) -> Optional[str]:
    start_value = str(activity.get("start_date_local", "")).strip()
    if not start_value:
        return None
    return start_value[:10]


def _activity_distance_m(activity: dict) -> Optional[float]:
    for key in ("distance", "distance_m", "distanceMeters"):
        value = activity.get(key)
        if value is None:
            continue
        try:
            distance = float(value)
        except (TypeError, ValueError):
            continue
        if distance > 0:
            return distance
    return None


def _activity_moving_time_s(activity: dict) -> Optional[float]:
    for key in ("moving_time", "elapsed_time"):
        value = activity.get(key)
        if value is None:
            continue
        try:
            seconds = float(value)
        except (TypeError, ValueError):
            continue
        if seconds > 0:
            return seconds
    return None


def _percent_hint_from_text(activity: dict) -> Optional[int]:
    haystack = " ".join(
        str(activity.get(key, "")).lower()
        for key in ("name", "description")
    )
    for percent, hints in KEYWORD_PERCENT_HINTS:
        if any(hint in haystack for hint in hints):
            return percent
    return None


def _nearest_band_from_pace(seconds_per_mile: float, current_5k_time: str) -> int:
    ladder = get_percentage_paces(current_5k_time)
    return min(
        PACE_BANDS,
        key=lambda percent: abs(ladder[percent]["seconds_per_mile"] - seconds_per_mile),
    )


def _mechanical_flag_for_percent(percent: int) -> str:
    if percent >= 110:
        return "high"
    if percent >= 100:
        return "medium"
    return "low"


def import_recent_history(
    api_key: str,
    current_5k_time: str,
    athlete_id: int = 0,
    days: int = 21,
) -> IntervalsImportResult:
    """Fetch recent Intervals.icu activities and map them into planner history rows."""
    activities = fetch_recent_activities(api_key=api_key, athlete_id=athlete_id, days=days)
    imported_rows: List[Dict[str, object]] = []
    candidate_activities = 0
    skipped_note_entries = 0
    skipped_non_runs = 0
    skipped_missing_fields = 0

    for activity in activities:
        if not _looks_like_completed_activity(activity):
            skipped_note_entries += 1
            continue

        candidate_activities += 1
        if _needs_detail(activity):
            try:
                activity = fetch_activity_detail(api_key=api_key, activity_id=str(activity["id"]))
            except ValueError:
                skipped_missing_fields += 1
                continue

        if not _is_run_activity(activity):
            skipped_non_runs += 1
            continue

        activity_date = _activity_date(activity)
        distance_m = _activity_distance_m(activity)
        moving_time_s = _activity_moving_time_s(activity)
        if activity_date is None or distance_m is None or moving_time_s is None:
            skipped_missing_fields += 1
            continue

        text_hint = _percent_hint_from_text(activity)
        if text_hint is None:
            seconds_per_mile = moving_time_s / (distance_m / 1609.344)
            guessed_percent = _nearest_band_from_pace(seconds_per_mile, current_5k_time)
        else:
            guessed_percent = text_hint

        equivalent_volume_m = min(int(round(distance_m)), PEAK_EQUIVALENTS_5K[guessed_percent])
        icu_load = activity.get("icu_training_load")
        try:
            load_score = float(icu_load) if icu_load is not None else 0.0
        except (TypeError, ValueError):
            load_score = 0.0
        if load_score <= 0:
            load_score = compute_load({guessed_percent: moving_time_s / 60.0}, 0.0)

        imported_rows.append(
            {
                "date": activity_date,
                "primary_percent": guessed_percent,
                "secondary_percents": "",
                "workout_text": str(activity.get("name") or "Intervals.icu activity"),
                "equivalent_volume_m": equivalent_volume_m,
                "load_score": round(load_score, 1),
                "load_class": classify_load(load_score),
                "mechanical_flag": _mechanical_flag_for_percent(guessed_percent),
            }
        )

    imported_rows.sort(key=lambda row: str(row["date"]), reverse=True)
    return IntervalsImportResult(
        imported_rows=imported_rows,
        scanned_entries=len(activities),
        candidate_activities=candidate_activities,
        skipped_note_entries=skipped_note_entries,
        skipped_non_runs=skipped_non_runs,
        skipped_missing_fields=skipped_missing_fields,
    )


def import_recent_history_rows(
    api_key: str,
    current_5k_time: str,
    athlete_id: int = 0,
    days: int = 21,
) -> List[Dict[str, object]]:
    """Backward-compatible wrapper that returns only mapped planner rows."""
    return import_recent_history(
        api_key=api_key,
        current_5k_time=current_5k_time,
        athlete_id=athlete_id,
        days=days,
    ).imported_rows
