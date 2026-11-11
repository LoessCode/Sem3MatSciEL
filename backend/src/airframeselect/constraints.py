"""Hard-constraint filter with plain-language rejection reasons."""
from __future__ import annotations

from typing import Any

from .data import PROP_COL, MaterialSet

CONSTRAINT_KEYS = [
    "max_density_kg_m3",
    "min_strength_MPa",
    "min_service_temp_C",
    "max_cost_usd_per_kg",
    "required_process",
]


def apply_constraints(
    ms: MaterialSet, constraints: dict[str, Any], allowed_processes: list[str] | None = None
) -> tuple[list[int], list[dict[str, Any]]]:
    """Split materials into (kept indices, excluded records with reasons).

    Limits are checked against each property's midpoint (documented design choice).
    """
    mid = ms.mid
    kept: list[int] = []
    excluded: list[dict[str, Any]] = []
    max_rho = constraints.get("max_density_kg_m3")
    min_sig = constraints.get("min_strength_MPa")
    min_temp = constraints.get("min_service_temp_C")
    max_cost = constraints.get("max_cost_usd_per_kg")
    req_proc = constraints.get("required_process")
    for i, rec in enumerate(ms.records):
        reasons: list[str] = []
        rho = mid[i, PROP_COL["density_kg_m3"]]
        sig = mid[i, PROP_COL["tensile_strength_MPa"]]
        temp = mid[i, PROP_COL["max_service_temp_C"]]
        cost = mid[i, PROP_COL["cost_usd_per_kg"]]
        if max_rho is not None and rho > max_rho:
            reasons.append(f"Too heavy: density about {rho:.0f} kg/m3 is above your limit of {max_rho:g} kg/m3.")
        if min_sig is not None and sig < min_sig:
            reasons.append(f"Too weak: tensile strength about {sig:.3g} MPa is below your minimum of {min_sig:g} MPa.")
        if min_temp is not None and temp < min_temp:
            reasons.append(f"Too heat-sensitive: it is only rated to about {temp:.0f} C, below your required {min_temp:g} C.")
        if max_cost is not None and cost > max_cost:
            reasons.append(f"Too expensive: about ${cost:.0f}/kg is above your limit of ${max_cost:g}/kg.")
        procs = rec["processes"]
        if req_proc:
            if req_proc not in procs:
                reasons.append(f"Cannot be made by the required process '{req_proc}' (it supports: {', '.join(procs)}).")
        elif allowed_processes is not None and not set(procs) & set(allowed_processes):
            reasons.append(
                "None of its manufacturing processes are suitable for this part "
                f"(it supports: {', '.join(procs)})."
            )
        if reasons:
            excluded.append({"id": rec["id"], "name": rec["name"], "family": rec["family"], "reasons": reasons})
        else:
            kept.append(i)
    return kept, excluded
