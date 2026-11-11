"""Explainable per-criterion contributions and plain-English summaries."""
from __future__ import annotations

import numpy as np

from .data import BENEFIT, CRITERIA
from .mcdm import minmax_normalise, normalise_weights

INDEX_PHRASES = {
    "beam_stiffness": "stiffness-to-weight as a beam",
    "beam_strength": "strength-to-weight as a beam",
    "panel_stiffness": "stiffness-to-weight as a panel",
    "panel_strength": "strength-to-weight as a panel",
    "tie_stiffness": "stiffness-to-weight in tension",
    "tie_strength": "strength-to-weight in tension",
}
# criterion -> (phrase when the material is strong on it, phrase when weak)
PHRASES = {
    "impact_resistance": ("good impact resistance", "poor impact resistance"),
    "max_service_temp": ("high service temperature", "low service temperature"),
    "cost": ("low cost", "high cost"),
    "embodied_energy": ("low embodied energy", "high embodied energy"),
    "recyclability": ("good recyclability", "poor recyclability"),
}


def contributions(X: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-criterion weighted contributions (n, 6): weight x min-max normalised value.

    Rows sum to the material's weighted-sum score. Returns (contributions, normalised).
    """
    norm = minmax_normalise(X, BENEFIT)
    w = normalise_weights(w)
    return norm * w[None, :], norm


# criterion -> noun used in "it loses points on ..."
NOUNS = {
    "performance_index": "weight efficiency",
    "impact_resistance": "impact resistance",
    "max_service_temp": "service temperature",
    "cost": "cost",
    "embodied_energy": "embodied energy",
    "recyclability": "recyclability",
}


def _phrase(criterion: str, strong: bool, index_id: str) -> str:
    if criterion == "performance_index":
        base = INDEX_PHRASES[index_id]
        return ("high " if strong else "low ") + base
    return PHRASES[criterion][0 if strong else 1]


def explain_material(
    name: str,
    rank: int,
    row: int,
    norm: np.ndarray,
    w: np.ndarray,
    index_id: str,
) -> dict:
    """Build the plain-English sentence for the material at matrix row `row`."""
    w = normalise_weights(w)
    # Advantage over the average candidate, weighted by how much the user cares.
    delta = w * (norm[row] - norm.mean(axis=0))
    order = np.argsort(-delta)
    strengths = [int(j) for j in order if delta[j] > 1e-3][:2]
    weak = [int(j) for j in order[::-1] if delta[j] < -1e-3][:1]
    ordinal = "first" if rank == 1 else f"#{rank}"
    verb = "ranks" if rank == 1 else "is placed"
    lead = f"{name} {verb} {ordinal}"
    if strengths:
        s_text = " and ".join(_phrase(CRITERIA[j], True, index_id) for j in strengths)
        sentence = f"{lead} mainly because of its {s_text}"
    else:
        sentence = f"{lead} because it is close to average on every criterion"
    if weak:
        sentence += f"; it loses points on {NOUNS[CRITERIA[weak[0]]]}."
    else:
        sentence += "; it has no notable weakness among the criteria you weighted."
    return {
        "sentence": sentence,
        "strengths": [CRITERIA[j] for j in strengths],
        "weaknesses": [CRITERIA[j] for j in weak],
    }
