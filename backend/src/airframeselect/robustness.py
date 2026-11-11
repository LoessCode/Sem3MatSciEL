"""Monte Carlo robustness analysis of a ranking.

Each trial draws (a) criteria weights from a Dirichlet distribution centred on the
user's weights and (b) every material property uniformly inside its [min, max] range,
then re-ranks all materials. Scores 1-5 (impact, recyclability) are treated as exact.
Everything is vectorised over trials.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .ashby import INDICES, index_value
from .data import BENEFIT, PROP_COL, MaterialSet
from .mcdm import normalise_weights, ranks_from_scores, topsis, weighted_sum

# Confidence thresholds on "rank stability": the share of trials in which a material lands
# within +/- STABILITY_BAND places of its baseline (non-random) rank.
STABILITY_BAND = 2
HIGH_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 0.40


def confidence_label(stability: float) -> str:
    if stability >= HIGH_THRESHOLD:
        return "High"
    if stability >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def score_matrix(X: np.ndarray, w: np.ndarray, method: str) -> np.ndarray:
    if method == "topsis":
        return topsis(X, w, BENEFIT)
    if method == "wsm":
        return weighted_sum(X, w, BENEFIT)
    raise ValueError(f"unknown method '{method}'")


def criteria_from_raw(index_id: str, raw: np.ndarray, impact: np.ndarray, recyc: np.ndarray) -> np.ndarray:
    """Build the (..., n, 6) decision matrix from raw property values (..., n, 6)."""
    prop_name, _ = INDICES[index_id]
    perf = index_value(index_id, raw[..., PROP_COL[prop_name]], raw[..., PROP_COL["density_kg_m3"]])
    shape = perf.shape
    return np.stack(
        [
            perf,
            np.broadcast_to(impact, shape),
            raw[..., PROP_COL["max_service_temp_C"]],
            raw[..., PROP_COL["cost_usd_per_kg"]],
            raw[..., PROP_COL["embodied_energy_MJ_per_kg"]],
            np.broadcast_to(recyc, shape),
        ],
        axis=-1,
    )


def run_monte_carlo(
    ms: MaterialSet,
    index_id: str,
    weights: np.ndarray,
    *,
    method: str = "topsis",
    trials: int = 2000,
    seed: int = 42,
    concentration: float | None = 20.0,
    range_scale: float = 1.0,
) -> dict[str, Any]:
    """Return per-material rank statistics.

    concentration: Dirichlet concentration (higher = weights stay closer to the user's);
        None keeps the weights fixed.
    range_scale: 1 samples the full [min, max] range, 0 collapses every range to its midpoint.
    """
    n = len(ms)
    if n == 0:
        raise ValueError("no materials to analyse")
    if trials < 1:
        raise ValueError("trials must be at least 1")
    if concentration is not None and concentration <= 0:
        raise ValueError("concentration must be positive")
    if not 0.0 <= range_scale <= 1.0:
        raise ValueError("range_scale must be between 0 and 1")
    w0 = normalise_weights(np.asarray(weights, dtype=float))
    rng = np.random.default_rng(seed)

    # Baseline (deterministic, midpoint) ranking.
    mid_raw = ms.mid
    X0 = criteria_from_raw(index_id, mid_raw, ms.impact, ms.recyc)
    base_scores = score_matrix(X0, w0, method)
    base_ranks = ranks_from_scores(base_scores)

    # Weights per trial.
    if concentration is None:
        W = np.broadcast_to(w0, (trials, len(w0)))
    else:
        W = rng.dirichlet(np.maximum(concentration * w0, 1e-9), size=trials)

    # Properties per trial, uniform in the (optionally shrunk) range.
    lo = mid_raw - range_scale * (mid_raw - ms.lo)
    hi = mid_raw + range_scale * (ms.hi - mid_raw)
    raw = lo[None] + rng.random((trials, n, lo.shape[1])) * (hi - lo)[None]
    X = criteria_from_raw(index_id, raw, ms.impact, ms.recyc)
    scores = score_matrix(X, W, method)
    ranks = ranks_from_scores(scores)  # (trials, n)

    dist = np.zeros((n, n))
    for r in range(1, n + 1):
        dist[:, r - 1] = (ranks == r).mean(axis=0)
    p1 = dist[:, 0]
    p3 = dist[:, : min(3, n)].sum(axis=1)
    median = np.median(ranks, axis=0)
    p05 = np.percentile(ranks, 5, axis=0)
    p95 = np.percentile(ranks, 95, axis=0)
    within = (np.abs(ranks - base_ranks[None, :]) <= STABILITY_BAND).mean(axis=0)
    return {
        "trials": trials,
        "seed": seed,
        "concentration": concentration,
        "range_scale": range_scale,
        "method": method,
        "baseline_scores": base_scores,
        "baseline_ranks": base_ranks,
        "rank_distribution": dist,
        "p_rank1": p1,
        "p_top3": p3,
        "median_rank": median,
        "rank_p05": p05,
        "rank_p95": p95,
        "stability": within,
        "confidence": [confidence_label(float(s)) for s in within],
    }
