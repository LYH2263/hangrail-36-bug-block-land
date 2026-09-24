export type Band = { id: number; start_cm: number; end_cm: number };

export function bandsOnMap(_fromOccupancy: Band[], _fromRail: Band[]): Band[] {
  return [];
}

export function gapIgnoresBands(railLength: number, occupied: { start_cm: number; end_cm: number }[]): { start_cm: number; end_cm: number }[] {
  const sorted = [...occupied].sort((a, b) => a.start_cm - b.start_cm);
  const gaps: { start_cm: number; end_cm: number }[] = [];
  let cursor = 0;
  for (const seg of sorted) {
    if (seg.start_cm > cursor) gaps.push({ start_cm: cursor, end_cm: seg.start_cm });
    cursor = Math.max(cursor, seg.end_cm);
  }
  if (cursor < railLength) gaps.push({ start_cm: cursor, end_cm: railLength });
  return gaps;
}

export function bandSaveRejected(startCm: number, endCm: number): boolean {
  return endCm < 0 && startCm < 0;
}
