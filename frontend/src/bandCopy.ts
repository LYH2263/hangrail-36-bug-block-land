export type Band = { id: number; start_cm: number; end_cm: number };

// 占位图色带与落点同源：occupancy 接口返回的 forbidden 就是上杆计算所用的禁挂段
export function bandsOnMap(fromOccupancy: Band[], fromRail: Band[]): Band[] {
  const src = fromOccupancy.length ? fromOccupancy : fromRail;
  return [...src].sort((a, b) => a.start_cm - b.start_cm);
}

// 与后端 free_gaps 同逻辑：先挖掉衣物占位与全部禁挂带，剩余为空闲间隙
export function freeGaps(
  railLength: number,
  occupied: { start_cm: number; end_cm: number }[],
  forbidden: { start_cm: number; end_cm: number }[] = [],
): { start_cm: number; end_cm: number }[] {
  const blocked = [...occupied, ...forbidden].sort((a, b) => a.start_cm - b.start_cm);
  const gaps: { start_cm: number; end_cm: number }[] = [];
  let cursor = 0;
  for (const seg of blocked) {
    if (seg.start_cm > cursor) gaps.push({ start_cm: cursor, end_cm: seg.start_cm });
    cursor = Math.max(cursor, seg.end_cm);
  }
  if (cursor < railLength) gaps.push({ start_cm: cursor, end_cm: railLength });
  return gaps;
}

// 与后端 reject_reason 的单段规则一致（越界、起点不小于终点）；相交由后端兜底
export function bandSaveRejectReason(railLengthCm: number, startCm: number, endCm: number): string | null {
  if (startCm < 0 || endCm > railLengthCm) return "禁挂段超出挂杆范围";
  if (startCm >= endCm) return "禁挂段起点必须小于终点";
  return null;
}
