
"""禁挂段：校验、挖空隙、占位图是否带回色带。"""
from __future__ import annotations

from app.services.rail_engine import Segment, overlaps


def bands_blocking_gaps(occupied: list[Segment], forbidden: list[Segment] | None) -> list[Segment]:
    """衣物占位与全部禁挂带一起参与挖空隙，衣段不得落入禁挂带。"""
    return list(occupied) + list(forbidden or [])


def reject_reason(rail_length: float, forbidden: list[Segment]) -> str | None:
    if not forbidden:
        return None
    for seg in forbidden:
        if seg.start_cm < 0 or seg.end_cm > rail_length:
            return "禁挂段超出挂杆范围"
        if seg.start_cm >= seg.end_cm:
            return "禁挂段起点必须小于终点"
    ordered = sorted(forbidden, key=lambda s: (s.start_cm, s.end_cm))
    for prev, nxt in zip(ordered, ordered[1:]):
        if overlaps(prev, nxt):
            return "禁挂段互相重叠"
    return None


def bands_for_map(rows: list) -> list:
    """占位图色带与落点同源：就是上杆计算读取的同一批禁挂段。"""
    return sorted(rows, key=lambda r: (r.start_cm, r.end_cm))
