import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { AshbyView } from "./components/AshbyView";
import { CompareView } from "./components/CompareView";
import { ParetoView } from "./components/ParetoView";
import { Methodology } from "./components/Methodology";
import { Results } from "./components/Results";
import { makeQuery, Selector } from "./components/Selector";
import { ErrorBox, Spinner } from "./components/ui";
import { PresenterContext, Caption } from "./presenter";
import type { Method, Presets, Query, RankResult, RobResult } from "./types";

type Tab = "analyse" | "ashby" | "pareto" | "compare" | "method";
const TABS: { id: Tab; label: string }[] = [
  { id: "analyse", label: "Recommend" },
  { id: "ashby", label: "Ashby chart" },
  { id: "pareto", label: "Pareto front" },
  { id: "compare", label: "Compare" },
  { id: "method", label: "Methodology" },
];

function tabFromHash(): Tab {
  const h = window.location.hash.replace("#", "");
  return (TABS.find((t) => t.id === h)?.id ?? "analyse") as Tab;
}

export default function App() {
  const [presets, setPresets] = useState<Presets | null>(null);
  const [fatal, setFatal] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>(tabFromHash);
  const [presenter, setPresenter] = useState(false);
  const [query, setQuery] = useState<Query | null>(null);
  const [ranQuery, setRanQuery] = useState<Query | null>(null);
  const [rank, setRank] = useState<RankResult | null>(null);
  const [rob, setRob] = useState<RobResult | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const reqId = useRef(0);

  useEffect(() => {
    const onHash = () => setTab(tabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const run = useCallback(async (q: Query) => {
    const id = ++reqId.current;
    setRunning(true);
    setRunError(null);
    try {
      const [r, b] = await Promise.all([api.rank(q), api.robustness(q)]);
      if (id !== reqId.current) return;
      setRank(r);
      setRob(b);
      setRanQuery(q);
    } catch (e) {
      if (id === reqId.current) setRunError((e as Error).message);
    } finally {
      if (id === reqId.current) setRunning(false);
    }
  }, []);

  const boot = useCallback(async () => {
    setFatal(null);
    try {
      const p = await api.presets();
      setPresets(p);
      const q = makeQuery(p, "arm", "balanced");
      setQuery(q);
      void run(q);
    } catch (e) {
      setFatal((e as Error).message);
    }
  }, [run]);

  useEffect(() => { void boot(); }, [boot]);

  const goTab = (t: Tab) => {
    setTab(t);
    window.history.replaceState(null, "", `#${t}`);
  };

  const onScenario = (id: string) => {
    if (!presets) return;
    const s = presets.scenarios.find((x) => x.id === id)!;
    const q = makeQuery(presets, s.part, s.profile, s.constraint_overrides);
    setQuery(q);
    goTab("analyse");
    void run(q);
  };

  const onMethod = (m: Method) => {
    if (!query) return;
    const q = { ...query, method: m };
    setQuery(q);
    void run(q);
  };

  const dirty = !!(query && ranQuery && JSON.stringify(query) !== JSON.stringify(ranQuery));

  const onTabKey = (e: React.KeyboardEvent, i: number) => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      const next = (i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length;
      goTab(TABS[next].id);
      document.getElementById(`tab-${TABS[next].id}`)?.focus();
    }
  };

  return (
    <PresenterContext.Provider value={presenter}>
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2">Skip to content</a>
      <header className="bg-navy-800 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">AirframeSelect</h1>
            <p className="text-xs text-sky-200">Material selection for drone airframes, with a confidence level</p>
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4 accent-oi-orange" checked={presenter} onChange={(e) => setPresenter(e.target.checked)} />
            Presenter mode
          </label>
        </div>
        <nav aria-label="Main" className="mx-auto max-w-7xl px-4">
          <div role="tablist" className="flex gap-1 overflow-x-auto">
            {TABS.map((t, i) => (
              <button
                key={t.id} id={`tab-${t.id}`} role="tab" aria-selected={tab === t.id} aria-controls="main"
                tabIndex={tab === t.id ? 0 : -1}
                onClick={() => goTab(t.id)} onKeyDown={(e) => onTabKey(e, i)}
                className={`whitespace-nowrap rounded-t-lg px-4 py-2 text-sm font-semibold focus-visible:ring-2 focus-visible:ring-white ${tab === t.id ? "bg-slate-100 text-navy-800" : "text-sky-100 hover:bg-navy-700"}`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      <main id="main" role="tabpanel" aria-labelledby={`tab-${tab}`} className="mx-auto max-w-7xl px-4 py-5">
        {fatal && <ErrorBox message={fatal} onRetry={boot} />}
        {!fatal && !presets && <Spinner label="Loading materials and presets" />}
        {presets && query && (
          <>
            {tab === "analyse" && (
              <div className="grid gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]">
                <div className="lg:sticky lg:top-4 lg:self-start">
                  <Selector presets={presets} query={query} setQuery={setQuery} onRun={() => run(query)} onScenario={onScenario} running={running} dirty={dirty} />
                </div>
                <div className="min-w-0">
                  {runError && <ErrorBox message={runError} onRetry={() => run(query)} />}
                  {running && !rank && <Spinner label="Ranking materials and running 2000 robustness trials" />}
                  {rank && (
                    <div className={running ? "opacity-60 transition-opacity" : ""} aria-busy={running}>
                      {running && <Spinner label="Updating" />}
                      <Results query={ranQuery ?? query} rank={rank} rob={rob} onMethod={onMethod} loadingMethod={running} />
                    </div>
                  )}
                </div>
              </div>
            )}
            {tab === "ashby" && (
              <section>
                <h2 className="text-lg font-bold text-navy-800">Ashby chart</h2>
                <Caption>A map of every material by weight and strength or stiffness: up and to the left is lighter for the same performance.</Caption>
                <AshbyView query={ranQuery ?? query} />
              </section>
            )}
            {tab === "pareto" && (
              <section>
                <h2 className="text-lg font-bold text-navy-800">Pareto front</h2>
                <Caption>Shows which materials are never beaten on both of two chosen factors, so you can see the real trade-offs.</Caption>
                <ParetoView query={ranQuery ?? query} />
              </section>
            )}
            {tab === "compare" && (
              <section>
                <h2 className="text-lg font-bold text-navy-800">Compare materials</h2>
                <Caption>Pick up to three materials and see them side by side; a bigger shape means better on more factors.</Caption>
                <CompareView part={(ranQuery ?? query).part} suggested={rank?.ranking.slice(0, 3).map((r) => r.id) ?? []} />
              </section>
            )}
            {tab === "method" && <Methodology presets={presets} />}
          </>
        )}
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-slate-500">
        AirframeSelect is an academic decision-support tool. Material values are typical figures that need verification before real design use. Runs fully offline.
      </footer>
    </PresenterContext.Provider>
  );
}
