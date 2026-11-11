import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip as RTooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { Caption } from "../presenter";
import { CRITERIA, type CriterionKey, type Method, type Query, type RankResult, type RankRow, type RobResult } from "../types";
import { CRITERION_COLORS, CRITERION_SHORT, FAMILY_COLORS, FAMILY_LABELS, fmt, pct } from "../theme";
import { ConfidenceBadge, Disclaimer, EmptyState, Tooltip } from "./ui";

interface Props {
  query: Query;
  rank: RankResult;
  rob: RobResult | null;
  onMethod: (m: Method) => void;
  loadingMethod: boolean;
}

const short = (s: string, n = 32) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

export function Results({ query, rank, rob, onMethod, loadingMethod }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const robById = useMemo(() => new Map((rob?.materials ?? []).map((m) => [m.id, m])), [rob]);
  const sel: RankRow | undefined = rank.ranking.find((r) => r.id === selectedId) ?? rank.ranking[0];
  const top = rank.ranking.slice(0, 8);

  const doExport = async (kind: "csv" | "pdf") => {
    setExporting(kind);
    setExportError(null);
    try { await api.download(kind, query); } catch (e) { setExportError((e as Error).message); }
    setExporting(null);
  };

  if (rank.ranking.length === 0) {
    return (
      <section className="panel" aria-live="polite">
        <h2 className="panel-title">Results</h2>
        <EmptyState title="No material passes all your limits">
          <p>{rank.message}</p>
          <ExcludedList rank={rank} defaultOpen />
        </EmptyState>
      </section>
    );
  }

  const winner = rank.ranking[0];
  const winnerRob = robById.get(winner.id);
  const agreement = rank.agreement!;

  const contribData = top.map((r) => ({ name: short(r.name), id: r.id, ...r.contributions }));
  const robData = top.map((r) => {
    const m = robById.get(r.id);
    return { name: short(r.name), id: r.id, "Chance of being #1": m ? +(m.p_rank1 * 100).toFixed(1) : 0, "Chance of top 3": m ? +(m.p_top3 * 100).toFixed(1) : 0 };
  });
  const selRob = sel ? robById.get(sel.id) : undefined;
  const distData = selRob ? selRob.rank_distribution.slice(0, 10).map((p, i) => ({ rank: `#${i + 1}`, pct: +(p * 100).toFixed(1) })) : [];

  return (
    <div className="space-y-4" aria-live="polite">
      {/* Headline */}
      <section className="panel border-l-4 border-l-oi-blue" aria-labelledby="headline">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {rank.inputs.part.name} · {rank.inputs.profile.name} · {rank.n_candidates} of {rank.n_total} materials qualify
        </p>
        <h2 id="headline" className="mt-1 flex flex-wrap items-center gap-2 text-xl font-bold text-navy-800">
          Top pick: {winner.name}
          <ConfidenceBadge level={winnerRob?.confidence} />
        </h2>
        <p className="mt-1 text-sm text-slate-700">{winner.explanation}</p>
        {rob?.summary && <p className="mt-1 text-sm text-slate-600">{rob.summary}</p>}
        <Caption>This is the recommendation, with a confidence badge that says how stable it is when we shake the inputs.</Caption>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className="btn-secondary" onClick={() => doExport("csv")} disabled={exporting !== null}>{exporting === "csv" ? "Preparing…" : "Download CSV"}</button>
          <button className="btn-secondary" onClick={() => doExport("pdf")} disabled={exporting !== null}>{exporting === "pdf" ? "Preparing…" : "Download PDF report"}</button>
          {exportError && <span role="alert" className="text-xs font-semibold text-red-700">{exportError}</span>}
        </div>
      </section>

      {/* Ranking table */}
      <section className="panel" aria-labelledby="ranking-title">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="ranking-title" className="panel-title">Ranking</h2>
          <div className="flex items-center gap-3">
            <div role="group" aria-label="Ranking method" className="inline-flex overflow-hidden rounded-lg border border-slate-300">
              {(["topsis", "wsm"] as Method[]).map((m) => (
                <button
                  key={m} onClick={() => onMethod(m)} aria-pressed={query.method === m} disabled={loadingMethod}
                  className={`px-3 py-1.5 text-xs font-semibold focus-visible:ring-2 focus-visible:ring-oi-blue ${query.method === m ? "bg-navy-700 text-white" : "bg-white text-ink hover:bg-slate-50"}`}
                >
                  {m === "topsis" ? "TOPSIS" : "Weighted sum"}
                </button>
              ))}
            </div>
          </div>
        </div>
        <Caption>Each material gets a score from 0 to 1 combining all six factors; higher is better.</Caption>
        <p className={`mt-2 inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs font-semibold ${agreement.top3_agree ? "border-emerald-600 bg-emerald-50 text-emerald-900" : "border-amber-600 bg-amber-50 text-amber-900"}`}>
          <span aria-hidden>{agreement.top3_agree ? "✔" : "≠"}</span>
          {agreement.top3_agree
            ? "Both methods agree on the top 3"
            : `Methods differ on the top 3 (overlap ${agreement.top3_overlap} of ${Math.min(3, rank.ranking.length)})`}
          <span className="font-normal">· rank correlation {fmt(agreement.spearman)}</span>
          <Tooltip text="TOPSIS and the weighted sum are two different ways of combining the factors. If they agree, the result does not depend on which one you trust. Rank correlation: 1 means identical order, 0 unrelated." label="About method agreement" />
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left text-sm">
            <caption className="sr-only">Materials ranked by {query.method === "topsis" ? "TOPSIS closeness" : "weighted-sum score"}</caption>
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th scope="col" className="py-2 pr-2">#</th>
                <th scope="col" className="py-2 pr-2">Material</th>
                <th scope="col" className="py-2 pr-2">Score</th>
                <th scope="col" className="py-2 pr-2">Chance #1</th>
                <th scope="col" className="py-2 pr-2">Confidence</th>
                <th scope="col" className="py-2">Flags</th>
              </tr>
            </thead>
            <tbody>
              {rank.ranking.map((r) => {
                const m = robById.get(r.id);
                const active = sel?.id === r.id;
                return (
                  <tr key={r.id} className={`border-b border-slate-100 ${active ? "bg-sky-50" : "hover:bg-slate-50"}`}>
                    <td className="py-2 pr-2 font-semibold tabular-nums">{r.rank}</td>
                    <td className="py-2 pr-2">
                      <button className="text-left font-medium text-navy-800 underline-offset-2 hover:underline focus-visible:ring-2" onClick={() => setSelectedId(r.id)} aria-pressed={active} aria-label={`${r.name}: show explanation`}>
                        {r.name}
                      </button>
                      <span className="ml-2 inline-flex items-center gap-1 text-[11px] text-slate-500">
                        <span className="inline-block h-2 w-2 rounded-full" style={{ background: FAMILY_COLORS[r.family] }} aria-hidden />
                        {FAMILY_LABELS[r.family]}
                      </span>
                    </td>
                    <td className="py-2 pr-2 tabular-nums">{fmt(r.score, 3)}</td>
                    <td className="py-2 pr-2 tabular-nums">{m ? pct(m.p_rank1) : "-"}</td>
                    <td className="py-2 pr-2"><ConfidenceBadge level={m?.confidence} /></td>
                    <td className="py-2 text-xs text-slate-600">{r.flags.length ? r.flags.join(" · ") : "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Explainer */}
      {sel && (
        <section className="panel" aria-labelledby="explain-title">
          <h2 id="explain-title" className="panel-title">Why these materials? <span className="font-normal text-slate-500">(selected: {sel.name})</span></h2>
          <Caption>Each bar is split by factor, so you can see what earned a material its score.</Caption>
          <p className="mt-2 rounded-lg bg-sky-50 p-3 text-sm text-navy-800">{sel.explanation}</p>
          {sel.caveat && <p className="mt-2 text-xs text-amber-900"><strong>Caveat:</strong> {sel.caveat}</p>}
          <p className="mt-1 text-xs text-slate-600">{sel.notes}</p>
          <div className="mt-3 h-72 w-full" role="img" aria-label="Stacked bars showing how each factor contributes to the score of the top eight materials">
            <ResponsiveContainer>
              <BarChart data={contribData} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => (v as number).toFixed(1)} />
                <YAxis type="category" dataKey="name" width={190} tick={{ fontSize: 12 }} />
                <RTooltip formatter={(v: number, name: string) => [v.toFixed(3), name]} />
                <Legend />
                {CRITERIA.map((c: CriterionKey) => (
                  <Bar key={c} dataKey={c} name={CRITERION_SHORT[c]} stackId="s" fill={CRITERION_COLORS[c]}>
                    {contribData.map((d) => <Cell key={d.id} fillOpacity={d.id === sel.id ? 1 : 0.75} stroke={d.id === sel.id ? "#12263a" : undefined} />)}
                  </Bar>
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Bars show weight × normalised value per factor (the weighted-sum breakdown). They explain both methods but add up exactly only to the weighted-sum score.
          </p>
        </section>
      )}

      {/* Robustness */}
      <section className="panel" aria-labelledby="rob-title">
        <h2 id="rob-title" className="panel-title">How confident is this ranking?</h2>
        <Caption>We re-ran the ranking {rob?.settings.trials ?? 2000} times with slightly different weights and data to see how often each material wins.</Caption>
        {!rob ? (
          <EmptyState title="Robustness analysis not available" />
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-700">
              In each trial the priorities were nudged and every property was drawn from its min-max range. High confidence means the material usually stays within two places of its baseline rank.
            </p>
            <div className="mt-3 h-72 w-full" role="img" aria-label="Bars showing the chance each of the top eight materials is ranked first and in the top three">
              <ResponsiveContainer>
                <BarChart data={robData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} unit="%" />
                  <YAxis type="category" dataKey="name" width={190} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v: number) => `${v}%`} />
                  <Legend />
                  <Bar dataKey="Chance of being #1" fill="#0072B2" />
                  <Bar dataKey="Chance of top 3" fill="#E69F00" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {selRob && sel && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold">Where {sel.name} lands across all trials</h3>
                <p className="text-xs text-slate-600">
                  Median rank {fmt(selRob.median_rank, 0)} (90% of trials between {fmt(selRob.rank_p05, 0)} and {fmt(selRob.rank_p95, 0)}). Baseline rank {selRob.baseline_rank}.
                </p>
                <div className="mt-2 h-44 w-full" role="img" aria-label={`Distribution of ranks for ${sel.name}`}>
                  <ResponsiveContainer>
                    <BarChart data={distData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="rank" />
                      <YAxis unit="%" />
                      <RTooltip formatter={(v: number) => `${v}%`} />
                      <Bar dataKey="pct" name="Share of trials" fill="#56B4E9" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      <ExcludedList rank={rank} />
      <Disclaimer />
    </div>
  );
}

export function ExcludedList({ rank, defaultOpen = false }: { rank: RankResult; defaultOpen?: boolean }) {
  return (
    <section className="panel" aria-labelledby="excl-title">
      <details open={defaultOpen}>
        <summary className="cursor-pointer text-base font-semibold text-navy-800" id="excl-title">
          Excluded materials ({rank.excluded.length})
        </summary>
        <Caption>These materials broke at least one of your hard limits, so they were never scored.</Caption>
        {rank.excluded.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">Nothing was excluded.</p>
        ) : (
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {rank.excluded.map((e) => (
              <li key={e.id} className="rounded-lg border border-slate-200 p-2 text-sm">
                <p className="font-semibold">{e.name}</p>
                <ul className="list-disc pl-5 text-xs text-slate-600">{e.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
              </li>
            ))}
          </ul>
        )}
      </details>
    </section>
  );
}
