"""Side-by-side comparison of up to three materials (radar-chart data)."""
from __future__ import annotations

import numpy as np

from .ashby import INDICES, index_ranges
from .data import BENEFIT, CRITERIA, PROP_COL, MaterialSet
from .mcdm import minmax_normalise

MAX_COMPARE = 3


def compare_materials(all_ms: MaterialSet, material_ids: list[str], index_id: str) -> dict:
    """Return normalised (0-1, higher = better on every axis) and raw values for each material.

    Normalisation is min-max over the whole database so that charts are comparable between
    runs; cost and embodied energy are inverted so a larger radar area is always better.
    """
    if not 1 <= len(material_ids) <= MAX_COMPARE:
        raise ValueError(f"choose between 1 and {MAX_COMPARE} materials")
    if len(set(material_ids)) != len(material_ids):
        raise ValueError("materials must be distinct")
    _, perf_mid, _ = index_ranges(index_id, all_ms)
    mid = all_ms.mid
    X = np.stack(
        [
            perf_mid,
            all_ms.impact,
            mid[:, PROP_COL["max_service_temp_C"]],
            mid[:, PROP_COL["cost_usd_per_kg"]],
            mid[:, PROP_COL["embodied_energy_MJ_per_kg"]],
            all_ms.recyc,
        ],
        axis=1,
    )
    norm = minmax_normalise(X, BENEFIT)
    series = []
    for mid_id in material_ids:
        i = all_ms.index_of(mid_id)
        rec = all_ms.records[i]
        series.append(
            {
                "id": rec["id"],
                "name": rec["name"],
                "family": rec["family"],
                "normalized": {c: float(norm[i, j]) for j, c in enumerate(CRITERIA)},
                "raw": {c: float(X[i, j]) for j, c in enumerate(CRITERIA)},
                "density_kg_m3": float(mid[i, PROP_COL["density_kg_m3"]]),
                "youngs_modulus_GPa": float(mid[i, PROP_COL["youngs_modulus_GPa"]]),
                "tensile_strength_MPa": float(mid[i, PROP_COL["tensile_strength_MPa"]]),
                "notes": rec["notes"],
                "property_basis": rec["property_basis"],
            }
        )
    return {"performance_index": index_id, "criteria": CRITERIA, "materials": series}
