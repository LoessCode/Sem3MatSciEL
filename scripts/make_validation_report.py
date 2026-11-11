#!/usr/bin/env python3
"""Run validation cases against the engine and write docs/VALIDATION.md."""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import json  # noqa: E402

import validate_data  # noqa: E402
from airframeselect.ashby import index_ranges  # noqa: E402
from airframeselect.data import CRITERIA, MaterialSet, all_materials, load_presets  # noqa: E402
from airframeselect.mcdm import ranks_from_scores, topsis, weighted_sum  # noqa: E402
from airframeselect.pipeline import run_ranking, run_robustness  # noqa: E402
from airframeselect.robustness import run_monte_carlo  # noqa: E402

BEN = np.array([True, True, False])
rows: list[tuple[str, bool, str]] = []


def case(name: str):
    def deco(fn):
        try:
            ok, detail = fn()
        except Exception as e:  # report, never crash the report generator
            ok, detail = False, f"exception: {e!r}"
        rows.append((name, bool(ok), detail))
        return fn
    return deco


@case("Data validator (schema, min<=max, family bounds, presets)")
def _():
    mats = json.loads((ROOT / "data" / "materials.json").read_text())
    presets = json.loads((ROOT / "data" / "presets.json").read_text())
    errs = validate_data.validate_materials(mats) + validate_data.validate_presets(presets, mats)
    return not errs, f"{len(mats['materials'])} materials, {len(errs)} errors"


@case("TOPSIS equals independent step-by-step arithmetic")
def _():
    M = [[250.0, 16.0, 12.0], [200.0, 16.0, 8.0], [300.0, 32.0, 16.0], [275.0, 32.0, 8.0]]
    W = [0.5, 0.3, 0.2]
    norms = [math.sqrt(sum(r[j] ** 2 for r in M)) for j in range(3)]
    v = [[M[i][j] / norms[j] * W[j] for j in range(3)] for i in range(4)]
    best = [max(c) if BEN[j] else min(c) for j, c in enumerate(zip(*v))]
    worst = [min(c) if BEN[j] else max(c) for j, c in enumerate(zip(*v))]
    exp = []
    for i in range(4):
        dp = math.sqrt(sum((v[i][j] - best[j]) ** 2 for j in range(3)))
        dn = math.sqrt(sum((v[i][j] - worst[j]) ** 2 for j in range(3)))
        exp.append(dn / (dp + dn))
    got = topsis(np.array(M), np.array(W), BEN)
    err = float(np.max(np.abs(got - np.array(exp))))
    return err < 1e-12, f"max abs error {err:.1e}"


@case("Rankings invariant to weight scaling (TOPSIS and weighted sum)")
def _():
    X = np.array([[250.0, 16.0, 12.0], [200.0, 16.0, 8.0], [300.0, 32.0, 16.0], [275.0, 32.0, 8.0]])
    w = np.array([0.5, 0.3, 0.2])
    ok = all(list(ranks_from_scores(f(X, w, BEN))) == list(ranks_from_scores(f(X, w * s, BEN))) for f in (topsis, weighted_sum) for s in (0.01, 7, 1000))
    return ok, "scales 0.01, 7, 1000"


@case("Ashby: carbon/epoxy beats Al 6061 and PLA on E^(1/2)/rho even worst-case vs best-case")
def _():
    ms = all_materials()
    lo, mid, hi = index_ranges("beam_stiffness", ms)
    c = ms.index_of("cfrp-qi")
    ok = all(lo[c] > hi[ms.index_of(o)] for o in ("al6061", "pla"))
    return ok, f"carbon min {lo[c]:.2f} vs Al6061 max {hi[ms.index_of('al6061')]:.2f}, PLA max {hi[ms.index_of('pla')]:.2f}"


@case("Ashby: Ti-6Al-4V beats Al 6061 on sigma^(2/3)/rho; steel is worse than Al on E^(1/2)/rho")
def _():
    ms = all_materials()
    lo_s, _, hi_s = index_ranges("beam_strength", ms)
    lo_b, _, hi_b = index_ranges("beam_stiffness", ms)
    t, a, s = ms.index_of("ti64"), ms.index_of("al6061"), ms.index_of("ss304")
    return lo_s[t] > hi_s[a] and lo_b[a] > hi_b[s], "interval-separated"


def kept():
    r = run_ranking("arm", "balanced")
    ms = all_materials()
    return ms.subset([ms.index_of(x["id"]) for x in r["ranking"]])


W6 = np.array([0.35, 0.20, 0.10, 0.15, 0.10, 0.10])


@case("Monte Carlo deterministic for a fixed seed")
def _():
    a = run_monte_carlo(kept(), "beam_stiffness", W6, seed=11, trials=800)
    b = run_monte_carlo(kept(), "beam_stiffness", W6, seed=11, trials=800)
    return bool(np.array_equal(a["rank_distribution"], b["rank_distribution"])), "identical rank distributions"


@case("Rank-probability matrix rows and columns sum to 1")
def _():
    d = run_monte_carlo(kept(), "beam_stiffness", W6, trials=800)["rank_distribution"]
    return bool(np.allclose(d.sum(0), 1) and np.allclose(d.sum(1), 1)), "doubly stochastic"


@case("Collapsed ranges + fixed weights: deterministic winner has P(rank 1) = 1")
def _():
    mc = run_monte_carlo(kept(), "beam_stiffness", W6, trials=300, concentration=None, range_scale=0.0)
    w = int(np.argmin(mc["baseline_ranks"]))
    return mc["p_rank1"][w] == 1.0, f"P(rank 1) = {mc['p_rank1'][w]:.3f}"


@case("Monte Carlo runtime: 60 materials x 2000 trials under 3 s")
def _():
    ms = all_materials()
    big = MaterialSet(list(ms.records) + [dict(r, id=r["id"] + "-x") for r in ms.records[:13]])
    t = time.perf_counter()
    run_monte_carlo(big, "beam_stiffness", W6, trials=2000)
    dt = time.perf_counter() - t
    return dt < 3.0, f"{dt:.2f} s for {len(big)} materials"


@case("Winner stability across 5 random seeds (arm / balanced)")
def _():
    p1 = []
    for seed in range(5):
        r = run_robustness("arm", "balanced", seed=seed, trials=2000)
        p1.append(r["materials"][0]["p_rank1"])
    spread = max(p1) - min(p1)
    return spread < 0.06, f"P(rank 1) of baseline winner: {', '.join(f'{x:.3f}' for x in p1)} (spread {spread:.3f})"


@case("Every excluded material carries a plain-language reason (all 6 parts)")
def _():
    n = 0
    for p in load_presets()["parts"]:
        r = run_ranking(p["id"], "balanced")
        if not all(e["reasons"] for e in r["excluded"]):
            return False, f"missing reason for part {p['id']}"
        n += len(r["excluded"])
    return True, f"{n} exclusions checked"


# ---- informational tables ----
presets = load_presets()
agree_rows = []
for p in presets["parts"]:
    for pr in presets["profiles"]:
        r = run_ranking(p["id"], pr["id"])
        a = r["agreement"]
        agree_rows.append((p["name"], pr["name"], r["ranking"][0]["name"], a["top1_agree"], a["top3_agree"], a["spearman"]))
n_top1 = sum(1 for x in agree_rows if x[3])
n_top3 = sum(1 for x in agree_rows if x[4])
mean_rho = float(np.mean([x[5] for x in agree_rows]))

scen_rows = []
for s in presets["scenarios"]:
    rb = run_robustness(s["part"], s["profile"], constraints=s["constraint_overrides"])
    top = rb["materials"][0]
    scen_rows.append((s["name"], top["name"], top["p_rank1"], top["p_top3"], top["confidence"]))

out = ["# Validation report", "",
       "Generated by `scripts/make_validation_report.py`. It re-runs the checks below against the current engine and data;",
       "the same properties are also asserted in `backend/tests/`. Material values are typical figures that still need",
       "verification, so these checks validate the **software and method**, not the datasheet accuracy.", "",
       "## 1. Verification cases", "", "| # | Case | Result | Detail |", "|---|------|--------|--------|"]
for i, (name, ok, detail) in enumerate(rows, 1):
    out.append(f"| {i} | {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
passed = sum(1 for r in rows if r[1])
out += ["", f"**{passed} of {len(rows)} cases passed.**", "",
        "## 2. Method agreement across all part x profile combinations", "",
        f"- Top-1 pick identical under TOPSIS and weighted sum: {n_top1} of {len(agree_rows)} combinations.",
        f"- Top-3 set identical: {n_top3} of {len(agree_rows)}.",
        f"- Mean Spearman rank correlation: {mean_rho:.2f}.", "",
        "| Part | Profile | TOPSIS top pick | Top-1 agree | Top-3 agree | Spearman |", "|---|---|---|---|---|---|"]
for part, prof, top, a1, a3, rho in agree_rows:
    out.append(f"| {part} | {prof} | {top} | {'yes' if a1 else 'no'} | {'yes' if a3 else 'no'} | {rho:.2f} |")
out += ["", "## 3. Demo scenarios: top pick and robustness (2000 trials, seed 42)", "",
        "| Scenario | Top pick | P(rank 1) | P(top 3) | Confidence |", "|---|---|---|---|---|"]
for name, top, p1, p3, conf in scen_rows:
    out.append(f"| {name} | {top} | {p1*100:.0f}% | {p3*100:.0f}% | {conf} |")
out += ["", "## 4. Reading these results honestly", "",
        "- A disagreement between TOPSIS and the weighted sum is not an error: the methods normalise differently, and the tool reports it so users can see how method-dependent a result is.",
        "- Natural materials such as bamboo laminate and plywood score well on specific stiffness and sustainability. Moisture, grain variation and joining are not modelled (see KNOWN_LIMITATIONS.md).",
        "- Confidence labels describe rank stability under the stated uncertainty model only.", ""]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "VALIDATION.md").write_text("\n".join(out), encoding="utf-8")
print(f"Wrote docs/VALIDATION.md: {passed}/{len(rows)} cases passed")
sys.exit(0 if passed == len(rows) else 1)
