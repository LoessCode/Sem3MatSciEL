import { useEffect, useMemo, useState } from "react";
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Legend, Tooltip as RTooltip } from "recharts";
import { api } from "../api";
import { Caption } from "../presenter";
import { CRITERIA, type CompareResult, type MaterialRecord } from "../types";
import { CRITERION_SHORT, fmt } from "../theme";
import { EmptyState, ErrorBox, Spinner } from "./ui";

const SERIES_COLORS = ["#0072B2", "#D55E00", "#009E73"];
const DASHES = ["", "6 3", "2 3"];

export function CompareView({ part, suggested }: { part: string; suggested: string[] }) {
  const [materials, setMaterials] = useState<MaterialRecord[]>([]);
  const [ids, setIds] = useState<string[]>(suggested.slice(0, 3));
  const [data, setData] = useState<CompareResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.materials().then((d) => setMaterials(d.materials)).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (ids.length === 0) { setData(null); return; }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api.compare(ids, part)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: Error) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [ids, part]);

  const toggle = (id: string) => setIds((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : cur.length >= 3 ? cur : [...cur, id]));
  const sorted = useMemo(() => [...materials].sort((a, b) => a.name.localeCompare(b.name)), [materials]);

  const radarData = data
    ? CRITERIA.map((c) => ({ axis: CRITERION_SHORT[c], ...Object.fromEntries(data.materials.map((m) => [m.name, +m.normalized[c].toFixed(3)])) }))
    : [];

  return (
    <div className="mt-2 grid gap-4 lg:grid-cols-[20rem_minmax(0,1fr)]">
      <fieldset className="panel max-h-[34rem] overflow-auto">
        <legend className="panel-title px-1">Pick up to 3 ({ids.length}/3)</legend>
        <ul className="mt-2 space-y-1">
          {sorted.map((m) => {
            const checked = ids.includes(m.id);
            const disabled = !checked && ids.length >= 3;
            return (
              <li key={m.id}>
                <label className={`flex items-center gap-2 rounded px-2 py-1 text-sm ${disabled ? "text-slate-400" : "cursor-pointer hover:bg-slate-50"}`}>
                  <input type="checkbox" className="h-4 w-4 accent-oi-blue" checked={checked} disabled={disabled} onChange={() => toggle(m.id)} />
                  {m.name}
                </label>
              </li>
            );
          })}
        </ul>
      </fieldset>
      <div className="min-w-0 space-y-4">
        {error && <ErrorBox message={error} />}
        {loading && !data && <Spinner label="Comparing" />}
        {ids.length === 0 && <EmptyState title="Choose at least one material" />}
        {data && ids.length > 0 && (
          <>
            <section className="panel" aria-label="Radar chart">
              <h3 className="panel-title">Shape comparison</h3>
              <p className="text-xs text-slate-600">Every axis is scaled 0–1 across all 47 materials, and cost and embodied energy are flipped so that outward is always better. Performance uses the index for your selected part.</p>
              <div className="mt-2 h-96 w-full" role="img" aria-label={`Radar chart comparing ${data.materials.map((m) => m.name).join(", ")}`}>
                <ResponsiveContainer>
                  <RadarChart data={radarData} outerRadius="72%">
                    <PolarGrid />
                    <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 1]} tickCount={5} tick={{ fontSize: 10 }} />
                    {data.materials.map((m, i) => (
                      <Radar key={m.id} name={m.name} dataKey={m.name} stroke={SERIES_COLORS[i]} strokeWidth={2.5} strokeDasharray={DASHES[i]} fill={SERIES_COLORS[i]} fillOpacity={0.15} />
                    ))}
                    <RTooltip />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </section>
            <section className="panel overflow-x-auto" aria-label="Comparison table">
              <h3 className="panel-title">Values side by side</h3>
              <table className="mt-2 w-full min-w-[28rem] text-left text-sm">
                <thead>
                  <tr className="border-b text-xs uppercase text-slate-500">
                    <th scope="col" className="py-2 pr-2">Property</th>
                    {data.materials.map((m) => <th key={m.id} scope="col" className="py-2 pr-2">{m.name}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Density (kg/m³)", (m: CompareResult["materials"][0]) => fmt(m.density_kg_m3, 0)],
                    ["Stiffness E (GPa)", (m: CompareResult["materials"][0]) => fmt(m.youngs_modulus_GPa, 2)],
                    ["Strength (MPa)", (m: CompareResult["materials"][0]) => fmt(m.tensile_strength_MPa, 1)],
                    ["Performance index", (m: CompareResult["materials"][0]) => fmt(m.raw.performance_index, 2)],
                    ["Impact resistance (1–5)", (m: CompareResult["materials"][0]) => fmt(m.raw.impact_resistance, 0)],
                    ["Max service temp (°C)", (m: CompareResult["materials"][0]) => fmt(m.raw.max_service_temp, 0)],
                    ["Cost ($/kg)", (m: CompareResult["materials"][0]) => fmt(m.raw.cost, 0)],
                    ["Embodied energy (MJ/kg)", (m: CompareResult["materials"][0]) => fmt(m.raw.embodied_energy, 0)],
                    ["Recyclability (1–5)", (m: CompareResult["materials"][0]) => fmt(m.raw.recyclability, 0)],
                  ].map(([label, f]) => (
                    <tr key={label as string} className="border-b border-slate-100">
                      <th scope="row" className="py-1.5 pr-2 font-medium">{label as string}</th>
                      {data.materials.map((m) => <td key={m.id} className="py-1.5 pr-2 tabular-nums">{(f as (m: CompareResult["materials"][0]) => string)(m)}</td>)}
                    </tr>
                  ))}
                  <tr>
                    <th scope="row" className="py-1.5 pr-2 align-top font-medium">Notes</th>
                    {data.materials.map((m) => <td key={m.id} className="py-1.5 pr-2 align-top text-xs text-slate-600">{m.notes}</td>)}
                  </tr>
                  <tr>
                    <th scope="row" className="py-1.5 pr-2 align-top font-medium">Data basis</th>
                    {data.materials.map((m) => <td key={m.id} className="py-1.5 pr-2 align-top text-xs text-slate-600">{m.property_basis}</td>)}
                  </tr>
                </tbody>
              </table>
            </section>
          </>
        )}
        <Caption>Values shown are midpoints of typical ranges and still need verification against datasheets.</Caption>
      </div>
    </div>
  );
}
