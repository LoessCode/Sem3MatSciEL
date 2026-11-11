import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip as RTooltip, XAxis, YAxis, LabelList } from "recharts";
import { api } from "../api";
import { Caption } from "../presenter";
import { CRITERIA, type ParetoResult, type Query } from "../types";
import { CRITERION_SHORT, fmt } from "../theme";
import { EmptyState, ErrorBox, Spinner } from "./ui";

export function ParetoView({ query }: { query: Query }) {
  const [x, setX] = useState("cost");
  const [y, setY] = useState("performance_index");
  const [data, setData] = useState<ParetoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const qKey = JSON.stringify(query);

  useEffect(() => {
    if (x === y) { setError("Choose two different criteria."); return; }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.pareto(query, x, y)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qKey, x, y]);

  const view = useMemo(() => {
    if (!data) return null;
    const front = data.points.filter((p) => p.pareto).sort((a, b) => a.x - b.x);
    const rest = data.points.filter((p) => !p.pareto);
    return { front, rest };
  }, [data]);

  const Sel = ({ label, value, set }: { label: string; value: string; set: (v: string) => void }) => (
    <label className="text-sm font-medium">
      {label}
      <select className="field mt-1" value={value} onChange={(e) => set(e.target.value)}>
        {CRITERIA.map((c) => <option key={c} value={c}>{CRITERION_SHORT[c]}</option>)}
      </select>
    </label>
  );

  return (
    <div className="mt-2 space-y-3">
      <div className="panel flex flex-wrap items-end gap-4">
        <Sel label="Horizontal axis" value={x} set={setX} />
        <Sel label="Vertical axis" value={y} set={setY} />
        <p className="max-w-md text-xs text-slate-600">
          A material is on the <strong>Pareto front</strong> if no other qualifying material is at least as good on both axes and better on one.
          Showing the {query.part} / {query.profile} candidates; change them on the Recommend tab.
        </p>
      </div>
      {error && <ErrorBox message={error} />}
      {loading && !data && <Spinner label="Computing Pareto front" />}
      {data && view && data.points.length === 0 && <EmptyState title="No qualifying materials">{data.message}</EmptyState>}
      {data && view && data.points.length > 0 && (
        <section className="panel" aria-label="Pareto chart">
          <p className="text-sm text-slate-700">
            {view.front.length} of {data.points.length} qualifying materials are on the front. For &quot;{data.x.label}&quot; {data.x.direction === "cost" ? "lower" : "higher"} is better; for &quot;{data.y.label}&quot; {data.y.direction === "cost" ? "lower" : "higher"} is better.
          </p>
          <div className="mt-3 h-[26rem] w-full" role="img" aria-label={`Scatter of ${data.y.label} against ${data.x.label} with the Pareto front highlighted`}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 16, right: 24, bottom: 28, left: 16 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name={data.x.label} tickFormatter={(v: number) => fmt(v, 1)} label={{ value: data.x.label, position: "insideBottom", offset: -16 }} />
                <YAxis type="number" dataKey="y" name={data.y.label} tickFormatter={(v: number) => fmt(v, 1)} label={{ value: data.y.label, angle: -90, position: "insideLeft" }} />
                <RTooltip content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const p = payload[0].payload as ParetoResult["points"][0];
                  return (
                    <div className="rounded-lg border border-slate-300 bg-white p-2 text-xs shadow-md">
                      <p className="font-semibold">{p.name}</p>
                      <p>{data.x.label}: {fmt(p.x, 2)}</p>
                      <p>{data.y.label}: {fmt(p.y, 2)}</p>
                      <p>{p.pareto ? "On the Pareto front" : `Dominated by ${p.dominated_by}`}</p>
                    </div>
                  );
                }} />
                <Legend verticalAlign="top" height={32} />
                <Scatter name="Dominated" data={view.rest} fill="#9aa5b1" fillOpacity={0.7} />
                <Scatter name="Pareto front" data={view.front} fill="#D55E00" line={{ stroke: "#D55E00", strokeWidth: 2 }} shape="diamond">
                  <LabelList dataKey="name" position="top" style={{ fontSize: 10, fill: "#12263a" }} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-semibold text-navy-800">Front members and who dominates the rest</summary>
            <ul className="mt-2 grid gap-1 text-xs sm:grid-cols-2">
              {data.points.map((p) => (
                <li key={p.id} className="rounded border border-slate-200 p-1.5">
                  <strong>{p.name}</strong> (rank {p.rank}): {p.pareto ? "on the front" : `dominated by ${p.dominated_by}`}
                </li>
              ))}
            </ul>
          </details>
        </section>
      )}
      <Caption>The front shows the best trade-offs only: anything below or behind it is beaten by a cheaper or better alternative.</Caption>
    </div>
  );
}
