import { useEffect, useState } from "react";
import { api } from "../api/client";
import { bandSaveRejectReason } from "../bandCopy";
type F = { id: number; start_cm: number; end_cm: number };
type R = { id: number; store_id: number; label: string; length_cm: number; forbidden_segments: F[] };
export default function RailsPage() {
  const [rows, setRows] = useState<R[]>([]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [railId, setRailId] = useState<number | "">("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api<R[]>("/rails").then(setRows);
  useEffect(() => { load(); }, []);

  async function addBand(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    if (railId === "") { setErr("请选择挂杆"); return; }
    const s = Number(start), en = Number(end);
    if (!Number.isFinite(s) || !Number.isFinite(en)) { setErr("请输入有效数字"); return; }
    const rail = rows.find(r => r.id === railId);
    const reason = rail ? bandSaveRejectReason(rail.length_cm, s, en) : null;
    if (reason) { setErr(reason); return; }
    setBusy(true);
    try {
      await api(`/rails/${railId}/forbidden`, {
        method: "POST",
        body: JSON.stringify({ start_cm: s, end_cm: en }),
      });
      setStart(""); setEnd("");
      await load();
    } catch (ex) {
      setErr(messageOf(ex));
    } finally {
      setBusy(false);
    }
  }

  async function removeBand(rid: number, fid: number) {
    setErr("");
    try {
      await api(`/rails/${rid}/forbidden/${fid}`, { method: "DELETE" });
      await load();
    } catch (ex) {
      setErr(messageOf(ex));
    }
  }

  return (<>
    <h2>挂杆</h2>
    <form className="toolbar" onSubmit={addBand}>
      <select value={railId} onChange={e => setRailId(e.target.value === "" ? "" : Number(e.target.value))}>
        <option value="">选择挂杆</option>
        {rows.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
      </select>
      <input type="number" min="0" placeholder="起点 cm" value={start}
        onChange={e => setStart(e.target.value)} style={{ width: 110 }} />
      <input type="number" min="0" placeholder="终点 cm" value={end}
        onChange={e => setEnd(e.target.value)} style={{ width: 110 }} />
      <button disabled={busy}>登记禁挂段</button>
      {err && <span className="err">{err}</span>}
    </form>
    <table className="table">
      <thead><tr><th>标签</th><th>门店</th><th>长度 cm</th><th>禁挂段（半开，cm）</th></tr></thead>
      <tbody>{rows.map(r => (
        <tr key={r.id}>
          <td>{r.label}</td>
          <td>{r.store_id}</td>
          <td className="mono">{r.length_cm}</td>
          <td>
            {r.forbidden_segments.length === 0 && <span className="tray-empty">无</span>}
            {r.forbidden_segments.map(f => (
              <span key={f.id} className="band-chip" title="禁挂带">
                <span className="mono">[{fmt(f.start_cm)}, {fmt(f.end_cm)})</span>
                <button type="button" className="band-chip-x"
                  onClick={() => removeBand(r.id, f.id)}>×</button>
              </span>
            ))}
          </td>
        </tr>
      ))}</tbody>
    </table>
  </>);
}

function fmt(n: number) { return Number.isInteger(n) ? String(n) : n.toFixed(1); }
function messageOf(ex: unknown) {
  try {
    const detail = JSON.parse((ex as Error).message)?.detail;
    return detail || (ex as Error).message;
  } catch {
    return (ex as Error).message;
  }
}
