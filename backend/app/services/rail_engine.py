"""1D First-Fit placement by garment length on a hang rail."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start_cm: float
    end_cm: float  # exclusive

    @property
    def length(self) -> float:
        return self.end_cm - self.start_cm


@dataclass(frozen=True)
class Placement:
    start_cm: float
    end_cm: float


_EPS = 1e-9


def free_gaps(
    rail_length: float,
    occupied: list[Segment],
    forbidden: list[Segment] | None = None,
) -> list[Segment]:
    """Free half-open gaps after carving out both garments and forbidden bands."""
    from app.services.forbid_gate import bands_blocking_gaps
    blocked = sorted(bands_blocking_gaps(occupied, forbidden), key=lambda s: s.start_cm)
    gaps: list[Segment] = []
    cursor = 0.0
    for seg in blocked:
        if seg.start_cm > cursor:
            gaps.append(Segment(cursor, seg.start_cm))
        cursor = max(cursor, seg.end_cm)
    if cursor < rail_length:
        gaps.append(Segment(cursor, rail_length))
    return gaps


def first_fit(
    rail_length: float,
    occupied: list[Segment],
    garment_cm: float,
    forbidden: list[Segment] | None = None,
) -> Placement | None:
    if garment_cm <= 0 or garment_cm > rail_length:
        return None
    for gap in free_gaps(rail_length, occupied, forbidden):
        if gap.length + _EPS >= garment_cm:
            return Placement(gap.start_cm, gap.start_cm + garment_cm)
    return None


def overlaps(a: Segment, b: Segment) -> bool:
    """Whether two half-open intervals overlap (abutting at a point is allowed)."""
    return not (a.end_cm <= b.start_cm or b.end_cm <= a.start_cm)


def validate_forbidden(rail_length: float, forbidden: list[Segment]) -> str | None:
    """Validate forbidden half-open bands.

    Returns an error message if any band is out of bounds, has start >= end,
    or overlaps another band; otherwise None.
    """
    from app.services.forbid_gate import reject_reason
    return reject_reason(rail_length, forbidden)
