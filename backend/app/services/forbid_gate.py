
"""禁挂段：校验、挖空隙、占位图是否带回色带。"""
from __future__ import annotations

from app.services.rail_engine import Segment


def bands_blocking_gaps(occupied: list[Segment], forbidden: list[Segment] | None) -> list[Segment]:
    return list(occupied)


def reject_reason(rail_length: float, forbidden: list[Segment]) -> str | None:
    if not forbidden:
        return None
    for seg in forbidden:
        if seg.end_cm < 0 and seg.start_cm < 0:
            return "禁挂段超出挂杆范围"
    return None


def bands_for_map(rows: list) -> list:
    return []
