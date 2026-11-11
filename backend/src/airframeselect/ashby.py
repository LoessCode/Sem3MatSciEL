"""Ashby performance indices with range propagation.

Units follow Ashby's convention: E in GPa, strength in MPa, density in Mg/m^3
(= kg/m^3 / 1000). Rankings do not depend on the unit choice; only the printed
values do.
"""
from __future__ import annotations

import numpy as np

from .data import PROP_COL, MaterialSet

# index id -> (property used, exponent on that property). Every index divides by density.
INDICES: dict[str, tuple[str, float]] = {
    "beam_stiffness": ("youngs_modulus_GPa", 0.5),
    "beam_strength": ("tensile_strength_MPa", 2.0 / 3.0),
    "panel_stiffness": ("youngs_modulus_GPa", 1.0 / 3.0),
    "panel_strength": ("tensile_strength_MPa", 0.5),
    "tie_stiffness": ("youngs_modulus_GPa", 1.0),
    "tie_strength": ("tensile_strength_MPa", 1.0),
}

INDEX_UNITS = {
    "beam_stiffness": "GPa^(1/2) / (Mg/m3)",
    "beam_strength": "MPa^(2/3) / (Mg/m3)",
    "panel_stiffness": "GPa^(1/3) / (Mg/m3)",
    "panel_strength": "MPa^(1/2) / (Mg/m3)",
    "tie_stiffness": "GPa / (Mg/m3)",
    "tie_strength": "MPa / (Mg/m3)",
}

_RHO = PROP_COL["density_kg_m3"]


def index_value(index_id: str, prop: np.ndarray, rho_kg_m3: np.ndarray) -> np.ndarray:
    """Evaluate the index for given property values (any broadcastable shapes)."""
    _, exponent = INDICES[index_id]
    return np.power(prop, exponent) / (np.asarray(rho_kg_m3) / 1000.0)


def index_ranges(index_id: str, ms: MaterialSet) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (min, mid, max) of the index for every material.

    mid uses the property midpoints. min pairs the lowest property with the highest
    density; max pairs the highest property with the lowest density (interval arithmetic).
    """
    prop_name, _ = INDICES[index_id]
    col = PROP_COL[prop_name]
    mid = index_value(index_id, ms.mid[:, col], ms.mid[:, _RHO])
    lo = index_value(index_id, ms.lo[:, col], ms.hi[:, _RHO])
    hi = index_value(index_id, ms.hi[:, col], ms.lo[:, _RHO])
    return lo, mid, hi


def guide_line(index_id: str, x_prop: str, y_prop: str, index_value_: float) -> dict | None:
    """Log-log guide line of constant index value on a chart with x=density (kg/m3) and y=y_prop.

    For index M = P^a / rho_Mg, constant M gives P = (M * rho_Mg)^(1/a), so on log10 axes
    the line has slope 1/a and, with density plotted in kg/m3, intercept (log10(M) - 3) / a.
    Returns None when the chart's y property is not the one the index uses.
    """
    prop_name, a = INDICES[index_id]
    if x_prop != "density_kg_m3" or y_prop != prop_name:
        return None
    slope = 1.0 / a
    intercept = (float(np.log10(index_value_)) - 3.0) / a
    return {
        "index": index_id,
        "property": prop_name,
        "exponent": a,
        "slope": slope,
        "intercept": intercept,
        "index_value": float(index_value_),
        "description": (
            f"Materials on this line have the same {index_id.replace('_', ' ')} index "
            f"({index_value_:.2f}); materials above/left of it perform better."
        ),
    }
