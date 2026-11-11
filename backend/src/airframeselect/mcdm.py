"""Multi-criteria decision methods: vector-normalised TOPSIS and min-max weighted sum.

Both functions accept optional leading batch dimensions so the Monte Carlo
robustness analysis can score thousands of trials in a single vectorised call:
    X: (..., n_alternatives, n_criteria)    w: (..., n_criteria)
"""
from __future__ import annotations

import numpy as np


def normalise_weights(w: np.ndarray) -> np.ndarray:
    w = np.asarray(w, dtype=float)
    total = w.sum(axis=-1, keepdims=True)
    if np.any(total <= 0):
        raise ValueError("weights must have a positive sum")
    return w / total


def topsis(X: np.ndarray, w: np.ndarray, benefit: np.ndarray) -> np.ndarray:
    """TOPSIS closeness coefficient in [0, 1] (higher is better)."""
    X = np.asarray(X, dtype=float)
    w = normalise_weights(w)
    norm = np.sqrt((X**2).sum(axis=-2, keepdims=True))
    norm = np.where(norm == 0, 1.0, norm)
    V = (X / norm) * w[..., None, :]
    vmax = V.max(axis=-2, keepdims=True)
    vmin = V.min(axis=-2, keepdims=True)
    ideal = np.where(benefit, vmax, vmin)
    anti = np.where(benefit, vmin, vmax)
    d_pos = np.sqrt(((V - ideal) ** 2).sum(axis=-1))
    d_neg = np.sqrt(((V - anti) ** 2).sum(axis=-1))
    denom = d_pos + d_neg
    safe = np.where(denom == 0, 1.0, denom)
    return np.where(denom == 0, 0.5, d_neg / safe)


def minmax_normalise(X: np.ndarray, benefit: np.ndarray) -> np.ndarray:
    """Min-max scale each criterion to [0, 1] where 1 is always the best value.

    Constant columns carry no information and are set to 0.5.
    """
    X = np.asarray(X, dtype=float)
    lo = X.min(axis=-2, keepdims=True)
    hi = X.max(axis=-2, keepdims=True)
    span = hi - lo
    safe = np.where(span == 0, 1.0, span)
    up = (X - lo) / safe
    scaled = np.where(benefit, up, 1.0 - up)
    return np.where(span == 0, 0.5, scaled)


def weighted_sum(X: np.ndarray, w: np.ndarray, benefit: np.ndarray) -> np.ndarray:
    """Weighted sum of min-max normalised criteria, in [0, 1] (higher is better)."""
    w = normalise_weights(w)
    return (minmax_normalise(X, benefit) * w[..., None, :]).sum(axis=-1)


def ranks_from_scores(scores: np.ndarray) -> np.ndarray:
    """1-based ranks along the last axis (1 = highest score); ties broken by position."""
    order = np.argsort(-scores, axis=-1, kind="stable")
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(1, scores.shape[-1] + 1) * np.ones_like(order), axis=-1)
    return ranks


def spearman(rank_a: np.ndarray, rank_b: np.ndarray) -> float:
    """Spearman rank correlation of two rank vectors without ties."""
    n = len(rank_a)
    if n < 2:
        return 1.0
    d = np.asarray(rank_a, float) - np.asarray(rank_b, float)
    return float(1.0 - 6.0 * np.sum(d**2) / (n * (n**2 - 1)))


def method_agreement(topsis_scores: np.ndarray, wsm_scores: np.ndarray) -> dict:
    """Compare the two methods' rankings: top-1, top-3 set overlap and Spearman correlation."""
    ra = ranks_from_scores(topsis_scores)
    rb = ranks_from_scores(wsm_scores)
    k = min(3, len(ra))
    top_a = set(np.argsort(ra)[:k].tolist())
    top_b = set(np.argsort(rb)[:k].tolist())
    return {
        "top1_agree": bool(np.argmin(ra) == np.argmin(rb)) if len(ra) else True,
        "top3_agree": top_a == top_b,
        "top3_overlap": len(top_a & top_b),
        "spearman": spearman(ra, rb),
    }
