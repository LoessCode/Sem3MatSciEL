import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, ErrorBar, LabelList, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip as RTooltip, XAxis, YAxis, Legend } from "recharts";
import { api } from "../api";
import { Caption } from "../presenter";
import type { AshbyPoint, AshbyResult, Query } from "../types";
import { FAMILY_COLORS, FAMILY_LABELS, fmt } from "../theme";
import { EmptyState, ErrorBox, Spinner } from "./ui";

const AXES = [
  { id: "density_vs_modulus", label: "Density vs stiffness (modulus)" },
  { id: "density_vs_strength", label: "Density vs strength" },
  { id: "cost_vs_strength", label: "Cost vs strength" },
];

function niceDomain(values: number[]): [number, number] {
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  return [Math.pow(10, Math.floor(Math.log10(lo))), Math.pow(10, Math.ceil(Math.log10(hi)))];
}

function logTicks([lo, hi]: [number, number]): number[] {
  const out: number[] = [];
  for (let e = Math.round(Math.log10(lo)); e <= Math.round(Math.log10(hi)); e++) {
    for (const m of [1, 2, 5]) {
      const v = m * Math.pow(10, e);
      if (v >= lo * 0.999 && v <= hi * 1.001) out.push(v);
    }
  }
  return out;
}

const tickFmt = (v: number) => (v >= 1000 ? `${v / 1000}k` : v < 0.01 ? v.toExponential(0) : `${+v.toPrecision(2)}`);

interface Datum { id: string; name: string; family: string; x: number; y: number; xErr: [number, number]; yErr: [number, number]; point: AshbyPoint; label?: string }

const toDatum = (p: AshbyPoint): Datum => ({
  id: p.id, name: p.name, family: p.family, x: p.x.mid, y: p.y.mid,
  xErr: [p.x.mid - p.x.min, p.x.max - p.x.mid], yErr: [p.y.mid - p.y.min, p.y.max - p.y.mid], point: p,
  label: p.top ? String(p.rank) : undefined,
});

export function AshbyView({ query }: { query: Query }) {
  const [axes, setAxes] = useState("density_vs_modulus");
  const [topN, setTopN] = useState(5);
  const [data, setData] = useState<AshbyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showExcluded, setShowExcluded] = useState(true);

  const qKey = JSON.stringify(query);
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.ashby(query, axes, topN)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qKey, axes, topN]);

  const view = useMemo(() => {
    if (!data) return null;
    const xs = data.points.flatMap((p) => [p.x.min, p.x.max]);
    const ys = data.points.flatMap((p) => [p.y.min, p.y.max]);
    const xd = niceDomain(xs);
    const yd = niceDomain(ys);
    const families = Array.from(new Set(data.points.map((p) => p.family)));
    const series = families.map((f) => ({ family: f, items: data.points.filter((p) => p.family === f && !p.excluded).map(toDatum) }));
    const excluded = data.points.filter((p) => p.excluded).map(toDatum);
    const tops = data.points.filter((p) => p.top).map(toDatum);
    let segment: { x: number; y: number }[] | undefined;
    if (data.guide) {
      const g = data.guide;
      const yAt = (x: number) => Math.pow(10, g.slope * Math.log10(x) + g.intercept);
      const xAt = (y: number) => Math.pow(10, (Math.log10(y) - g.intercept) / g.slope);
      const xa = Math.max(xd[0], xAt(yd[0]));
      const xb = Math.min(xd[1], xAt(yd[1]));
      if (xa < xb) segment = [{ x: xa, y: yAt(xa) }, { x: xb, y: yAt(xb) }];
    }
    return { xd, yd, series, excluded, tops, segment, xt: logTicks(xd), yt: logTicks(yd) };
  }, [data]);

  return (
    <div className="mt-2 space-y-3">
      <div className="panel flex flex-wrap items-end gap-4">
        <label className="text-sm font-medium">
          Axes
          <select className="field mt-1" value={axes} onChange={(e) => setAxes(e.target.value)}>
            {AXES.map((a) => <option key={a.id} value={a.id}>{a.label}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium">
          Highlight top {topN}
          <input type="range" min={0} max={10} value={topN} onChange={(e) => setTopN(Number(e.target.value))} className="mt-2 block w-40 accent-oi-blue" />
        </label>
        <label className="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" className="h-4 w-4 accent-oi-blue" checked={showExcluded} onChange={(e) => setShowExcluded(e.target.checked)} />
          Show excluded materials (grey)
        </label>
        <p className="text-xs text-slate-600">Showing results for <strong>{query.part}</strong> / <strong>{query.profile}</strong>; change them on the Recommend tab.</p>
      </div>

      {error && <ErrorBox message={error} />}
      {loading && !data && <Spinner label="Loading chart" />}
      {data && view && (
        <section className="panel" aria-label="Ashby chart">
          <p className="text-sm text-slate-700">
            Both axes are logarithmic. Each dot is a material at its typical value; the cross-hair bars show its min-max range.
            {data.guide
              ? <> The dashed line joins materials with the same <strong>{data.performance_index.label}</strong> index ({data.performance_index.formula}) as {data.guide.through}; materials above or to the left of it do better on that index.</>
              : <> A guide line is shown only on the chart whose axes match the performance index ({data.performance_index.label}: choose <em>{data.performance_index.id.includes("stiffness") ? "density vs stiffness" : "density vs strength"}</em>).</>}
          </p>
          {data.message && <p className="mt-2 text-xs text-amber-900">{data.message}</p>}
          <div className="mt-3 h-[28rem] w-full" role="img" aria-label={`Ashby chart of ${data.y.label} against ${data.x.label} on logarithmic axes for ${data.points.length} materials`}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 16, right: 24, bottom: 28, left: 16 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name={data.x.label} scale="log" domain={view.xd} ticks={view.xt} tickFormatter={tickFmt} allowDataOverflow
                  label={{ value: `${data.x.label} (${data.x.unit})`, position: "insideBottom", offset: -16 }} />
                <YAxis type="number" dataKey="y" name={data.y.label} scale="log" domain={view.yd} ticks={view.yt} tickFormatter={tickFmt} allowDataOverflow
                  label={{ value: `${data.y.label} (${data.y.unit})`, angle: -90, position: "insideLeft" }} />
                <RTooltip content={<AshbyTooltip data={data} />} cursor={{ strokeDasharray: "3 3" }} />
                <Legend verticalAlign="top" height={40} />
                {showExcluded && (
                  <Scatter name="Excluded by limits" data={view.excluded} fill="#9aa5b1" fillOpacity={0.55} shape="circle">
                    <ErrorBar dataKey="xErr" direction="x" stroke="#c3cad2" width={0} />
                    <ErrorBar dataKey="yErr" direction="y" stroke="#c3cad2" width={0} />
                  </Scatter>
                )}
                {view.series.map((s) => (
                  <Scatter key={s.family} name={FAMILY_LABELS[s.family]} data={s.items} fill={FAMILY_COLORS[s.family]} fillOpacity={0.85}>
                    <ErrorBar dataKey="xErr" direction="x" stroke={FAMILY_COLORS[s.family]} strokeOpacity={0.45} width={0} />
                    <ErrorBar dataKey="yErr" direction="y" stroke={FAMILY_COLORS[s.family]} strokeOpacity={0.45} width={0} />
                  </Scatter>
                ))}
                {view.tops.length > 0 && (
                  <Scatter name={`Top ${view.tops.length} picks (numbered by rank)`} data={view.tops} fill="none" stroke="#12263a" strokeWidth={2.5} shape="circle" legendType="circle">
                    <LabelList dataKey="label" position="top" style={{ fontSize: 11, fontWeight: 600, fill: "#12263a" }} />
                  </Scatter>
                )}
                {view.segment && <ReferenceLine segment={view.segment} stroke="#12263a" strokeDasharray="6 4" strokeWidth={2} ifOverflow="hidden" />}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          {data.guide && (
            <p className="mt-1 text-xs text-slate-600">
              Guide line: log(y) = {fmt(data.guide.slope)} × log(x) + {fmt(data.guide.intercept)} (slope {fmt(data.guide.slope)} comes from the index exponent). Index value {fmt(data.guide.index_value)} {data.performance_index.units}.
            </p>
          )}
          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-semibold text-navy-800">Show the chart data as a table</summary>
            <div className="mt-2 max-h-72 overflow-auto">
              <table className="w-full text-left text-xs">
                <thead><tr className="border-b"><th scope="col" className="py-1">Material</th><th scope="col">{data.x.label} range</th><th scope="col">{data.y.label} range</th><th scope="col">Status</th></tr></thead>
                <tbody>
                  {data.points.map((p) => (
                    <tr key={p.id} className="border-b border-slate-100">
                      <td className="py-1 pr-2">{p.name}</td>
                      <td>{fmt(p.x.min, 3)} – {fmt(p.x.max, 3)} {data.x.unit}</td>
                      <td>{fmt(p.y.min, 3)} – {fmt(p.y.max, 3)} {data.y.unit}</td>
                      <td>{p.excluded ? "Excluded" : `Rank ${p.rank}`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>
      )}
      {data && data.points.length === 0 && <EmptyState title="No materials to plot" />}
      <Caption>Wood, foams and composites sit high and to the left (light for their strength); metals sit lower and to the right.</Caption>
    </div>
  );
}

function AshbyTooltip({ active, payload, data }: { active?: boolean; payload?: { payload: Datum }[]; data: AshbyResult }) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0].payload.point;
  return (
    <div className="rounded-lg border border-slate-300 bg-white p-2 text-xs shadow-md">
      <p className="font-semibold">{p.name}</p>
      <p className="text-slate-600">{FAMILY_LABELS[p.family]} · {p.excluded ? "excluded by your limits" : `rank ${p.rank}`}</p>
      <p>{data.x.label}: {fmt(p.x.min, 3)} – {fmt(p.x.max, 3)} {data.x.unit}</p>
      <p>{data.y.label}: {fmt(p.y.min, 3)} – {fmt(p.y.max, 3)} {data.y.unit}</p>
    </div>
  );
}
