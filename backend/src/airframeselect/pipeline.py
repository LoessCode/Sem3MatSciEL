"""High-level orchestration used by the API, CLI and exports."""
from __future__ import annotations

from typing import Any

import numpy as np

from .ashby import INDEX_UNITS, INDICES, guide_line, index_ranges
from .compare import compare_materials
from .constraints import CONSTRAINT_KEYS, apply_constraints
from .data import (
    BENEFIT, CRITERIA, PROP_COL, PROPS, MaterialSet, all_materials, get_part, get_profile, load_presets,
)
from .explain import contributions, explain_material
from .pareto import criteria_columns, pareto_front
from .mcdm import method_agreement, normalise_weights, ranks_from_scores, topsis, weighted_sum
from .robustness import criteria_from_raw, run_monte_carlo

METHODS = ("topsis", "wsm")


class InputError(ValueError):
    """Raised for invalid user input (mapped to HTTP 422/400 by the API)."""


def _lookup(fn, ident: str, kind: str) -> dict[str, Any]:
    try:
        return fn(ident)
    except KeyError:
        raise InputError(f"unknown {kind} '{ident}'") from None


def resolve_inputs(
    part_id: str,
    profile_id: str = "balanced",
    weights: dict[str, float] | None = None,
    constraints: dict[str, Any] | None = None,
    method: str = "topsis",
) -> dict[str, Any]:
    """Merge part defaults, profile modifiers and user overrides into explicit inputs."""
    part = _lookup(get_part, part_id, "part")
    profile = _lookup(get_profile, profile_id, "profile")
    if method not in METHODS:
        raise InputError(f"unknown method '{method}' (choose from {', '.join(METHODS)})")
    w = {c: part["weights"][c] * profile["modifiers"][c] for c in CRITERIA}
    for k, v in (weights or {}).items():
        if k not in CRITERIA:
            raise InputError(f"unknown weight '{k}' (choose from {', '.join(CRITERIA)})")
        if v < 0:
            raise InputError(f"weight '{k}' must not be negative")
        w[k] = float(v)
    if (weights or {}) and sum(w.values()) <= 0:
        raise InputError("at least one weight must be above zero")
    total = sum(w.values())
    w = {c: w[c] / total for c in CRITERIA}
    cons = dict(part["constraints"])
    for k, v in (constraints or {}).items():
        if k not in CONSTRAINT_KEYS:
            raise InputError(f"unknown constraint '{k}'")
        if k == "required_process":
            allowed = {"fdm", "layup", "machining", "injection", "sheet-forming", "cnc-cut"}
            if v is not None and v not in allowed:
                raise InputError(f"unknown process '{v}' (choose from {', '.join(sorted(allowed))})")
        elif v is not None and v <= 0:
            raise InputError(f"constraint '{k}' must be positive")
        cons[k] = v
    idx = part["performance_index"]
    return {
        "part": {"id": part["id"], "name": part["name"], "load_case": part["load_case"], "rationale": part["rationale"]},
        "profile": {"id": profile["id"], "name": profile["name"], "description": profile["description"]},
        "weights": w,
        "constraints": cons,
        "allowed_processes": part["allowed_processes"],
        "performance_index": {"id": idx, "label": load_presets()["indices"][idx]["label"],
                              "formula": load_presets()["indices"][idx]["formula"], "units": INDEX_UNITS[idx]},
        "method": method,
    }


def _flags(rec: dict, mid_row: np.ndarray, idx_range: tuple[float, float], cons: dict) -> list[str]:
    flags: list[str] = []
    lo, hi = idx_range
    if lo > 0 and hi / lo >= 1.4:
        flags.append("Wide data range")
    min_temp = cons.get("min_service_temp_C")
    if min_temp is not None and mid_row[PROP_COL["max_service_temp_C"]] - min_temp <= 15:
        flags.append("Small temperature margin")
    if mid_row[PROP_COL["cost_usd_per_kg"]] > 100:
        flags.append("High cost")
    if "sandwich core" in rec["property_basis"]:
        flags.append("Sandwich core only")
    if rec.get("caveat"):
        flags.append("Has caveat")
    return flags


def run_ranking(
    part_id: str,
    profile_id: str = "balanced",
    weights: dict[str, float] | None = None,
    constraints: dict[str, Any] | None = None,
    method: str = "topsis",
    _ms: MaterialSet | None = None,
) -> dict[str, Any]:
    inputs = resolve_inputs(part_id, profile_id, weights, constraints, method)
    ms = _ms or all_materials()
    kept, excluded = apply_constraints(ms, inputs["constraints"], inputs["allowed_processes"])
    index_id = inputs["performance_index"]["id"]
    result: dict[str, Any] = {
        "inputs": inputs,
        "n_total": len(ms),
        "n_candidates": len(kept),
        "excluded": excluded,
        "ranking": [],
        "agreement": None,
        "message": None,
    }
    if not kept:
        result["message"] = "No material satisfies all the constraints. Relax one or more limits (see the exclusion reasons)."
        return result
    sub = ms.subset(kept)
    w = np.array([inputs["weights"][c] for c in CRITERIA])
    X = criteria_from_raw(index_id, sub.mid, sub.impact, sub.recyc)
    t_scores = topsis(X, w, BENEFIT)
    w_scores = weighted_sum(X, w, BENEFIT)
    t_ranks = ranks_from_scores(t_scores)
    w_ranks = ranks_from_scores(w_scores)
    primary = t_scores if method == "topsis" else w_scores
    p_ranks = t_ranks if method == "topsis" else w_ranks
    contrib, norm = contributions(X, w)
    i_lo, i_mid, i_hi = index_ranges(index_id, sub)
    rows = []
    for i in np.argsort(p_ranks):
        rec = sub.records[i]
        expl = explain_material(rec["name"], int(p_ranks[i]), int(i), norm, w, index_id)
        mid_row = sub.mid[i]
        rows.append(
            {
                "rank": int(p_ranks[i]),
                "id": rec["id"],
                "name": rec["name"],
                "family": rec["family"],
                "processes": rec["processes"],
                "score": float(primary[i]),
                "topsis_score": float(t_scores[i]),
                "wsm_score": float(w_scores[i]),
                "topsis_rank": int(t_ranks[i]),
                "wsm_rank": int(w_ranks[i]),
                "performance_index": {"min": float(i_lo[i]), "mid": float(i_mid[i]), "max": float(i_hi[i])},
                "values": {
                    **{p: float(mid_row[j]) for j, p in enumerate(PROPS)},
                    "impact_resistance": float(sub.impact[i]),
                    "recyclability": float(sub.recyc[i]),
                },
                "flags": _flags(rec, mid_row, (float(i_lo[i]), float(i_hi[i])), inputs["constraints"]),
                "contributions": {c: float(contrib[i, j]) for j, c in enumerate(CRITERIA)},
                "explanation": expl["sentence"],
                "strengths": expl["strengths"],
                "weaknesses": expl["weaknesses"],
                "notes": rec["notes"],
                "caveat": rec.get("caveat"),
            }
        )
    result["ranking"] = rows
    result["agreement"] = method_agreement(t_scores, w_scores)
    return result


def run_robustness(
    part_id: str,
    profile_id: str = "balanced",
    weights: dict[str, float] | None = None,
    constraints: dict[str, Any] | None = None,
    method: str = "topsis",
    trials: int = 2000,
    seed: int = 42,
    concentration: float | None = 20.0,
    range_scale: float = 1.0,
) -> dict[str, Any]:
    base = run_ranking(part_id, profile_id, weights, constraints, method)
    out: dict[str, Any] = {
        "inputs": base["inputs"],
        "settings": {"trials": trials, "seed": seed, "concentration": concentration, "range_scale": range_scale, "method": method},
        "n_candidates": base["n_candidates"],
        "materials": [],
        "winner": None,
        "message": base["message"],
    }
    if not base["ranking"]:
        return out
    ms = all_materials().subset([all_materials().index_of(r["id"]) for r in base["ranking"]])
    w = np.array([base["inputs"]["weights"][c] for c in CRITERIA])
    mc = run_monte_carlo(
        ms, base["inputs"]["performance_index"]["id"], w, method=method, trials=trials,
        seed=seed, concentration=concentration, range_scale=range_scale,
    )
    rows = []
    for i, r in enumerate(base["ranking"]):
        rows.append(
            {
                "id": r["id"],
                "name": r["name"],
                "family": r["family"],
                "baseline_rank": r["rank"],
                "p_rank1": float(mc["p_rank1"][i]),
                "p_top3": float(mc["p_top3"][i]),
                "median_rank": float(mc["median_rank"][i]),
                "rank_p05": float(mc["rank_p05"][i]),
                "rank_p95": float(mc["rank_p95"][i]),
                "stability": float(mc["stability"][i]),
                "confidence": mc["confidence"][i],
                "rank_distribution": [float(x) for x in mc["rank_distribution"][i]],
            }
        )
    out["materials"] = rows
    best = max(rows, key=lambda x: x["p_rank1"])
    top = rows[0]
    out["winner"] = {
        "baseline_top_id": top["id"], "baseline_top_name": top["name"], "baseline_top_p_rank1": top["p_rank1"],
        "most_likely_id": best["id"], "most_likely_name": best["name"], "most_likely_p_rank1": best["p_rank1"],
    }
    out["summary"] = (
        f"{top['name']} (the baseline #1) came first in {top['p_rank1']*100:.0f}% of {trials} random trials "
        f"and in the top 3 in {top['p_top3']*100:.0f}%."
    )
    return out


def run_compare(material_ids: list[str], part_id: str = "arm") -> dict[str, Any]:
    part = _lookup(get_part, part_id, "part")
    ms = all_materials()
    try:
        return compare_materials(ms, material_ids, part["performance_index"])
    except KeyError as e:
        raise InputError(f"unknown material {e}") from None
    except ValueError as e:
        raise InputError(str(e)) from None


ASHBY_AXES = {
    "density_vs_strength": ("density_kg_m3", "tensile_strength_MPa"),
    "density_vs_modulus": ("density_kg_m3", "youngs_modulus_GPa"),
    "cost_vs_strength": ("cost_usd_per_kg", "tensile_strength_MPa"),
}
AXIS_LABELS = {
    "density_kg_m3": ("Density", "kg/m3"),
    "tensile_strength_MPa": ("Tensile strength", "MPa"),
    "youngs_modulus_GPa": ("Young's modulus", "GPa"),
    "cost_usd_per_kg": ("Cost", "USD/kg"),
}


def run_ashby(
    part_id: str,
    profile_id: str = "balanced",
    weights: dict[str, float] | None = None,
    constraints: dict[str, Any] | None = None,
    method: str = "topsis",
    axes: str = "density_vs_modulus",
    top_n: int = 5,
) -> dict[str, Any]:
    if axes not in ASHBY_AXES:
        raise InputError(f"unknown axes '{axes}' (choose from {', '.join(ASHBY_AXES)})")
    if top_n < 0:
        raise InputError("top_n must not be negative")
    base = run_ranking(part_id, profile_id, weights, constraints, method)
    ms = all_materials()
    xp, yp = ASHBY_AXES[axes]
    xc, yc = PROP_COL[xp], PROP_COL[yp]
    rank_of = {r["id"]: r["rank"] for r in base["ranking"]}
    points = []
    for i, rec in enumerate(ms.records):
        rk = rank_of.get(rec["id"])
        points.append(
            {
                "id": rec["id"], "name": rec["name"], "family": rec["family"],
                "x": {"min": float(ms.lo[i, xc]), "max": float(ms.hi[i, xc]), "mid": float(ms.mid[i, xc])},
                "y": {"min": float(ms.lo[i, yc]), "max": float(ms.hi[i, yc]), "mid": float(ms.mid[i, yc])},
                "excluded": rk is None,
                "rank": rk,
                "top": rk is not None and rk <= top_n,
            }
        )
    guide = None
    if base["ranking"]:
        index_id = base["inputs"]["performance_index"]["id"]
        top_row = base["ranking"][0]
        guide = guide_line(index_id, xp, yp, top_row["performance_index"]["mid"])
        if guide:
            guide["through"] = top_row["name"]
    return {
        "axes": axes,
        "x": {"property": xp, "label": AXIS_LABELS[xp][0], "unit": AXIS_LABELS[xp][1]},
        "y": {"property": yp, "label": AXIS_LABELS[yp][0], "unit": AXIS_LABELS[yp][1]},
        "performance_index": base["inputs"]["performance_index"],
        "points": points,
        "guide": guide,
        "top_ids": [r["id"] for r in base["ranking"][:top_n]],
        "message": base["message"],
    }


def run_pareto(
    part_id: str,
    profile_id: str = "balanced",
    weights: dict[str, float] | None = None,
    constraints: dict[str, Any] | None = None,
    method: str = "topsis",
    x_criterion: str = "cost",
    y_criterion: str = "performance_index",
) -> dict[str, Any]:
    """Pareto front of the feasible candidates over two chosen criteria."""
    for c in (x_criterion, y_criterion):
        if c not in CRITERIA:
            raise InputError(f"unknown criterion '{c}' (choose from {', '.join(CRITERIA)})")
    if x_criterion == y_criterion:
        raise InputError("choose two different criteria")
    base = run_ranking(part_id, profile_id, weights, constraints, method)
    meta = {c["key"]: c for c in load_presets()["criteria"]}
    out: dict[str, Any] = {
        "x": {"key": x_criterion, "label": meta[x_criterion]["label"], "direction": meta[x_criterion]["direction"]},
        "y": {"key": y_criterion, "label": meta[y_criterion]["label"], "direction": meta[y_criterion]["direction"]},
        "points": [], "front_ids": [], "message": base["message"],
    }
    if not base["ranking"]:
        return out
    ms = all_materials()
    sub = ms.subset([ms.index_of(r["id"]) for r in base["ranking"]])
    X = criteria_from_raw(base["inputs"]["performance_index"]["id"], sub.mid, sub.impact, sub.recyc)
    cols = criteria_columns([x_criterion, y_criterion])
    front, dom = pareto_front(X, cols)
    for i, r in enumerate(base["ranking"]):
        out["points"].append({
            "id": r["id"], "name": r["name"], "family": r["family"], "rank": r["rank"],
            "x": float(X[i, cols[0]]), "y": float(X[i, cols[1]]),
            "pareto": bool(front[i]),
            "dominated_by": base["ranking"][dom[i]]["name"] if dom[i] is not None else None,
        })
    out["front_ids"] = [p["id"] for p in out["points"] if p["pareto"]]
    return out
