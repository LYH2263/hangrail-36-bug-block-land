"""禁挂段：校验、挖空隙、占位图是否带回色带。"""
from __future__ import annotations

import math

from app.services.rail_engine import Segment


def bands_blocking_gaps(
    occupied: list[Segment], forbidden: list[Segment] | None
) -> list[Segment]:
    """合并衣物段与禁挂段，返回排序后互不相交的阻塞区间集合。

    半开区间在端点相接（[a,b) 与 [b,c)）视为不重叠，但合并后对挖空
    间隙的结果没有影响，故一并归并。
    """
    blocked = sorted(occupied + (list(forbidden) if forbidden else []), key=lambda s: s.start_cm)
    merged: list[Segment] = []
    for seg in blocked:
        if merged and seg.start_cm <= merged[-1].end_cm:
            merged[-1] = Segment(merged[-1].start_cm, max(merged[-1].end_cm, seg.end_cm))
        else:
            merged.append(seg)
    return merged


def reject_reason(rail_length: float, forbidden: list[Segment]) -> str | None:
    """校验禁挂半开区间，非法时返回中文原因，合法返回 None。"""
    if not forbidden:
        return None
    for seg in forbidden:
        if not (math.isfinite(seg.start_cm) and math.isfinite(seg.end_cm)):
            return "禁挂段坐标必须为有限数字"
    for seg in forbidden:
        if seg.start_cm >= seg.end_cm:
            return "禁挂段起点必须小于终点"
    for seg in forbidden:
        if seg.start_cm < 0 or seg.end_cm > rail_length:
            return "禁挂段超出挂杆范围"
    ordered = sorted(forbidden, key=lambda s: s.start_cm)
    for prev, seg in zip(ordered, ordered[1:]):
        # 半开区间：端点相接（prev.end == seg.start）不算相交
        if seg.start_cm < prev.end_cm:
            return "禁挂段之间不得重叠"
    return None


def bands_for_map(rows: list) -> list:
    """占位图禁挂带：与上杆落点同源，直接透传库里的禁挂段行。"""
    return list(rows)
