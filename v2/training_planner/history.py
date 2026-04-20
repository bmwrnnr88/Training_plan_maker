from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, List, Optional

from models import SessionRecord


def _parse_session_date(raw_date: str) -> Optional[date]:
    """Parse a session date in ISO format and ignore invalid values."""
    if not raw_date:
        return None

    try:
        return datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_ago(session: SessionRecord) -> Optional[int]:
    session_date = _parse_session_date(session.date)
    if session_date is None:
        return None
    return (date.today() - session_date).days


def get_recent_sessions(history: Iterable[SessionRecord], days: int) -> List[SessionRecord]:
    """Return sessions from the last N days."""
    recent_sessions: List[SessionRecord] = []

    for session in history:
        delta_days = _days_ago(session)
        if delta_days is None:
            continue
        if 0 <= delta_days <= days:
            recent_sessions.append(session)

    recent_sessions.sort(key=lambda session: session.date, reverse=True)
    return recent_sessions


def count_percent_exposures(history: Iterable[SessionRecord], percent: int, window_days: int) -> int:
    """Count how often a percent appeared recently as primary or secondary work."""
    exposures = 0

    for session in get_recent_sessions(history, window_days):
        if session.primary_percent == percent or percent in session.secondary_percents:
            exposures += 1

    return exposures


def days_since_percent(history: Iterable[SessionRecord], percent: int) -> Optional[int]:
    """Return days since the percent was last touched, if ever."""
    deltas: List[int] = []

    for session in history:
        if session.primary_percent != percent and percent not in session.secondary_percents:
            continue
        delta_days = _days_ago(session)
        if delta_days is not None and delta_days >= 0:
            deltas.append(delta_days)

    return min(deltas) if deltas else None


def recent_best_equivalent(
    history: Iterable[SessionRecord],
    percent: int,
    window_days: int = 42,
) -> Optional[int]:
    """Return the best recently demonstrated equivalent volume for a percent."""
    best_equivalent: Optional[int] = None

    for session in get_recent_sessions(history, window_days):
        if session.primary_percent != percent and percent not in session.secondary_percents:
            continue
        if best_equivalent is None or session.equivalent_volume_m > best_equivalent:
            best_equivalent = session.equivalent_volume_m

    return best_equivalent
