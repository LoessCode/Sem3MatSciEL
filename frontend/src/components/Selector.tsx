import { useState } from "react";
import { Caption } from "../presenter";
import { CRITERIA, type Constraints, type CriterionKey, type Presets, type Query } from "../types";
import { CRITERION_COLORS, PROCESS_LABELS } from "../theme";
import { Tooltip } from "./ui";

export function defaultWeights(presets: Presets, partId: string, profileId: string): Record<CriterionKey, number> {
  const part = presets.parts.find((p) => p.id === partId)!;
  const profile = presets.profiles.find((p) => p.id === profileId)!;
  const raw = Object.fromEntries(CRITERIA.map((c) => [c, part.weights[c] * profile.modifiers[c]])) as Record<CriterionKey, number>;
  const total = CRITERIA.reduce((s, c) => s + raw[c], 0);
  return Object.fromEntries(CRITERIA.map((c) => [c, Math.round((raw[c] / total) * 100)])) as Record<CriterionKey, number>;
}

export function makeQuery(presets: Presets, partId: string, profileId: string, overrides: Partial<Constraints> = {}): Query {
  const part = presets.parts.find((p) => p.id === partId)!;
  return {
    part: partId,
    profile: profileId,
    method: "topsis",
    weights: defaultWeights(presets, partId, profileId),
    constraints: { ...part.constraints, ...overrides },
  };
}

const STEPS = ["Part", "Mission", "Limits", "Priorities", "Run"];

interface Props {
  presets: Presets;
  query: Query;
  setQuery: (q: Query) => void;
  onRun: () => void;
  onScenario: (id: string) => void;
  running: boolean;
  dirty: boolean;
}

export function Selector({ presets, query, setQuery, onRun, onScenario, running, dirty }: Props) {
  const [step, setStep] = useState(0);
  const part = presets.parts.find((p) => p.id === query.part)!;
  const profile = presets.profiles.find((p) => p.id === query.profile)!;
  const totalW = CRITERIA.reduce((s, c) => s + query.weights[c], 0);

  const pickPart = (id: string) => setQuery(makeQuery(presets, id, query.profile));
  const pickProfile = (id: string) =>
    setQuery({ ...query, profile: id, weights: defaultWeights(presets, query.part, id) });
  const setCons = (k: keyof Constraints, v: number | string | null) =>
    setQuery({ ...query, constraints: { ...query.constraints, [k]: v } });

  const numField = (k: Exclude<keyof Constraints, "required_process">, label: string, unit: string, help: string) => (
    <label className="block text-sm">
      <span className="font-medium">{label}</span>
      <Tooltip text={help} label={`About ${label}`} />
      <span className="mt-1 flex items-center gap-2">
        <input
          type="number" min={0} inputMode="decimal" className="field" placeholder="No limit"
          value={query.constraints[k] ?? ""}
          onChange={(e) => setCons(k, e.target.value === "" ? null : Number(e.target.value))}
        />
        <span className="w-14 text-xs text-slate-500">{unit}</span>
      </span>
    </label>
  );

  return (
    <section className="panel" aria-labelledby="selector-title">
      <h2 id="selector-title" className="panel-title">Choose your inputs</h2>
      <Caption>Four quick choices describe the part and what matters; then we rank 47 materials and say how sure we are.</Caption>

      <div className="mt-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">One-click demos</p>
        <div className="mt-1 flex flex-col gap-2">
          {presets.scenarios.map((s) => (
            <button key={s.id} className="btn-secondary justify-start text-left" onClick={() => onScenario(s.id)} title={s.description}>
              <span aria-hidden>▶</span> {s.name}
            </button>
          ))}
        </div>
      </div>

      <ol className="mt-5 flex items-center justify-between gap-1" aria-label="Steps">
        {STEPS.map((name, i) => (
          <li key={name} className="flex-1">
            <button
              onClick={() => setStep(i)}
              aria-current={i === step ? "step" : undefined}
              className={`w-full rounded-md px-1 py-1.5 text-center text-xs font-semibold transition focus-visible:ring-2 focus-visible:ring-oi-blue ${
                i === step ? "bg-navy-700 text-white" : i < step ? "bg-sky-100 text-navy-800" : "bg-slate-100 text-slate-600"
              }`}
            >
              <span className="block text-[10px] opacity-80">{i + 1}</span>
              {name}
            </button>
          </li>
        ))}
      </ol>

      <div className="mt-4 min-h-[16rem]">
        {step === 0 && (
          <fieldset>
            <legend className="text-sm font-semibold">1. Which part are you choosing a material for?</legend>
            <div className="mt-2 grid gap-2">
              {presets.parts.map((p) => (
                <label key={p.id} className={`cursor-pointer rounded-lg border p-3 text-sm ${p.id === query.part ? "border-oi-blue bg-sky-50" : "border-slate-200 hover:bg-slate-50"}`}>
                  <input type="radio" name="part" className="mr-2 accent-oi-blue" checked={p.id === query.part} onChange={() => pickPart(p.id)} />
                  <span className="font-semibold">{p.name}</span>
                  <span className="mt-1 block pl-6 text-xs text-slate-600">{p.load_case}</span>
                </label>
              ))}
            </div>
            <p className="mt-3 rounded-md bg-slate-50 p-2 text-xs text-slate-700"><strong>Why this index?</strong> {part.rationale}</p>
          </fieldset>
        )}

        {step === 1 && (
          <fieldset>
            <legend className="text-sm font-semibold">2. What kind of mission is it?</legend>
            <div className="mt-2 grid gap-2">
              {presets.profiles.map((p) => (
                <label key={p.id} className={`cursor-pointer rounded-lg border p-3 text-sm ${p.id === query.profile ? "border-oi-blue bg-sky-50" : "border-slate-200 hover:bg-slate-50"}`}>
                  <input type="radio" name="profile" className="mr-2 accent-oi-blue" checked={p.id === query.profile} onChange={() => pickProfile(p.id)} />
                  <span className="font-semibold">{p.name}</span>
                  <span className="mt-1 block pl-6 text-xs text-slate-600">{p.description}</span>
                </label>
              ))}
            </div>
          </fieldset>
        )}

        {step === 2 && (
          <div>
            <h3 className="text-sm font-semibold">3. Hard limits (a material that breaks any limit is removed)</h3>
            <div className="mt-2 grid gap-3">
              {numField("max_density_kg_m3", "Maximum density", "kg/m³", "Heavier materials are removed. Water is 1000 kg/m³; aluminium is about 2700.")}
              {numField("min_strength_MPa", "Minimum strength", "MPa", "Materials weaker than this are removed. Foams and cork are very weak; printed plastics are around 40 MPa.")}
              {numField("min_service_temp_C", "Minimum service temperature", "°C", "The part must survive at least this temperature, for example near motors, batteries or in a hot car.")}
              {numField("max_cost_usd_per_kg", "Maximum cost", "$/kg", "Materials costing more per kilogram are removed.")}
              <label className="block text-sm">
                <span className="font-medium">Required manufacturing process</span>
                <Tooltip text="Only materials that can be made with this method are kept. Choose 3D printing to see only printable materials." label="About required process" />
                <select className="field mt-1" value={query.constraints.required_process ?? ""} onChange={(e) => setCons("required_process", e.target.value || null)}>
                  <option value="">Any process</option>
                  {Object.entries(PROCESS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </label>
            </div>
            <button className="btn-secondary mt-3" onClick={() => setQuery({ ...query, constraints: { ...part.constraints } })}>Reset to part defaults</button>
          </div>
        )}

        {step === 3 && (
          <div>
            <h3 className="text-sm font-semibold">4. How much does each factor matter?</h3>
            <p className="mt-1 text-xs text-slate-600">Sliders start from the part and mission. Only the proportions matter; they are rescaled to 100%.</p>
            <ul className="mt-3 space-y-4">
              {presets.criteria.map((c) => {
                const v = query.weights[c.key];
                const share = totalW > 0 ? Math.round((v / totalW) * 100) : 0;
                return (
                  <li key={c.key}>
                    <label htmlFor={`w-${c.key}`} className="flex items-center justify-between text-sm font-medium">
                      <span>
                        <span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: CRITERION_COLORS[c.key] }} aria-hidden />
                        {c.label}
                        <Tooltip text={c.plain} label={`What is ${c.label}?`} />
                      </span>
                      <span className="tabular-nums text-slate-700">{share}%</span>
                    </label>
                    <input
                      id={`w-${c.key}`} type="range" min={0} max={100} step={1} value={v}
                      aria-valuetext={`${share} percent`}
                      className="mt-1 w-full accent-oi-blue"
                      onChange={(e) => setQuery({ ...query, weights: { ...query.weights, [c.key]: Number(e.target.value) } })}
                    />
                  </li>
                );
              })}
            </ul>
            {totalW === 0 && <p role="alert" className="mt-2 text-xs font-semibold text-red-700">Set at least one slider above zero.</p>}
            <button className="btn-secondary mt-3" onClick={() => setQuery({ ...query, weights: defaultWeights(presets, query.part, query.profile) })}>Reset to mission defaults</button>
          </div>
        )}

        {step === 4 && (
          <div className="text-sm">
            <h3 className="font-semibold">5. Ready to run</h3>
            <dl className="mt-2 space-y-1 rounded-lg bg-slate-50 p-3 text-xs">
              <div><dt className="inline font-semibold">Part: </dt><dd className="inline">{part.name}</dd></div>
              <div><dt className="inline font-semibold">Mission: </dt><dd className="inline">{profile.name}</dd></div>
              <div><dt className="inline font-semibold">Performance index: </dt><dd className="inline">{presets.indices[part.performance_index].label} ({presets.indices[part.performance_index].formula})</dd></div>
              <div><dt className="inline font-semibold">Limits: </dt><dd className="inline">{
                [
                  query.constraints.max_density_kg_m3 != null && `density ≤ ${query.constraints.max_density_kg_m3} kg/m³`,
                  query.constraints.min_strength_MPa != null && `strength ≥ ${query.constraints.min_strength_MPa} MPa`,
                  query.constraints.min_service_temp_C != null && `temperature ≥ ${query.constraints.min_service_temp_C} °C`,
                  query.constraints.max_cost_usd_per_kg != null && `cost ≤ $${query.constraints.max_cost_usd_per_kg}/kg`,
                  query.constraints.required_process && `process: ${PROCESS_LABELS[query.constraints.required_process]}`,
                ].filter(Boolean).join(", ") || "none"
              }</dd></div>
            </dl>
            {dirty && <p className="mt-2 text-xs font-semibold text-amber-800">Inputs changed since the last result: press Run to update.</p>}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between gap-2 border-t border-slate-200 pt-3">
        <button className="btn-secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>Back</button>
        {step < 4 ? (
          <button className="btn-secondary" onClick={() => setStep(step + 1)}>Next</button>
        ) : null}
        <button className="btn-primary" onClick={onRun} disabled={running || totalW === 0}>
          {running ? "Running…" : dirty ? "Run (inputs changed)" : "Run"}
        </button>
      </div>
    </section>
  );
}
