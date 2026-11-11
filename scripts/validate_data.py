#!/usr/bin/env python3
"""Validate data/materials.json and data/presets.json.

Checks: schema and missing fields, min <= max, family-level plausibility bounds,
score ranges, process vocabulary, and preset cross-references.
Run directly (exit code 0 = OK) or import `validate_materials` / `validate_presets`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSES = {"fdm", "layup", "machining", "injection", "sheet-forming", "cnc-cut"}
FAMILIES = {
    "printable-polymer", "printable-composite", "fibre-composite",
    "metal", "natural-core", "recycled",
}
PROPS = [
    "density_kg_m3", "youngs_modulus_GPa", "tensile_strength_MPa",
    "max_service_temp_C", "cost_usd_per_kg", "embodied_energy_MJ_per_kg",
]
SCORES = ["impact_resistance", "recyclability"]
REQUIRED = ["id", "name", "family", "processes", "notes", "property_basis", "data_status", "properties", "scores"]

# Family-level plausibility bounds: property -> (low, high) that every min and max must sit inside.
BOUNDS: dict[str, dict[str, tuple[float, float]]] = {
    "printable-polymer": {
        "density_kg_m3": (800, 2000), "youngs_modulus_GPa": (0.01, 6), "tensile_strength_MPa": (10, 150),
        "max_service_temp_C": (40, 300), "cost_usd_per_kg": (5, 1500), "embodied_energy_MJ_per_kg": (30, 350)},
    "printable-composite": {
        "density_kg_m3": (900, 1800), "youngs_modulus_GPa": (2, 25), "tensile_strength_MPa": (30, 200),
        "max_service_temp_C": (50, 300), "cost_usd_per_kg": (15, 1500), "embodied_energy_MJ_per_kg": (50, 450)},
    "fibre-composite": {
        "density_kg_m3": (1000, 2200), "youngs_modulus_GPa": (2, 120), "tensile_strength_MPa": (30, 1500),
        "max_service_temp_C": (40, 250), "cost_usd_per_kg": (3, 600), "embodied_energy_MJ_per_kg": (20, 500)},
    "metal": {
        "density_kg_m3": (1500, 9000), "youngs_modulus_GPa": (30, 250), "tensile_strength_MPa": (150, 1500),
        "max_service_temp_C": (80, 1000), "cost_usd_per_kg": (1, 400), "embodied_energy_MJ_per_kg": (20, 1200)},
    "natural-core": {
        "density_kg_m3": (10, 1500), "youngs_modulus_GPa": (0.001, 30), "tensile_strength_MPa": (0.05, 200),
        "max_service_temp_C": (50, 700), "cost_usd_per_kg": (1, 600), "embodied_energy_MJ_per_kg": (2, 700)},
    "recycled": {
        "density_kg_m3": (800, 2000), "youngs_modulus_GPa": (0.3, 6), "tensile_strength_MPa": (10, 150),
        "max_service_temp_C": (40, 250), "cost_usd_per_kg": (3, 300), "embodied_energy_MJ_per_kg": (5, 250)},
}


def validate_materials(doc: dict) -> list[str]:
    errors: list[str] = []
    mats = doc.get("materials")
    if not isinstance(mats, list):
        return ["top-level 'materials' list is missing"]
    if not 45 <= len(mats) <= 60:
        errors.append(f"expected 45-60 materials, found {len(mats)}")
    seen: set[str] = set()
    for i, m in enumerate(mats):
        tag = m.get("id", f"#{i}") if isinstance(m, dict) else f"#{i}"
        if not isinstance(m, dict):
            errors.append(f"{tag}: record is not an object")
            continue
        for key in REQUIRED:
            if key not in m or m[key] in (None, "", [], {}):
                errors.append(f"{tag}: missing field '{key}'")
        if tag in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(tag)
        fam = m.get("family")
        if fam not in FAMILIES:
            errors.append(f"{tag}: unknown family '{fam}'")
        if m.get("data_status") != "typical-value-needs-verification":
            errors.append(f"{tag}: data_status must be 'typical-value-needs-verification'")
        procs = m.get("processes") or []
        bad = [p for p in procs if p not in PROCESSES]
        if bad:
            errors.append(f"{tag}: unknown processes {bad}")
        props = m.get("properties") or {}
        for p in PROPS:
            rng = props.get(p)
            if not isinstance(rng, dict) or "min" not in rng or "max" not in rng:
                errors.append(f"{tag}: property '{p}' needs {{min,max}}")
                continue
            lo, hi = rng["min"], rng["max"]
            if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (lo, hi)):
                errors.append(f"{tag}: property '{p}' min/max must be numbers")
                continue
            if lo > hi:
                errors.append(f"{tag}: property '{p}' has min > max ({lo} > {hi})")
            if lo <= 0:
                errors.append(f"{tag}: property '{p}' must be positive")
            if fam in BOUNDS:
                b_lo, b_hi = BOUNDS[fam][p]
                if lo < b_lo or hi > b_hi:
                    errors.append(f"{tag}: property '{p}' [{lo}, {hi}] outside {fam} plausibility bounds [{b_lo}, {b_hi}]")
        scores = m.get("scores") or {}
        for s in SCORES:
            v = scores.get(s)
            if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 5:
                errors.append(f"{tag}: score '{s}' must be an integer 1-5")
    return errors


def validate_presets(presets: dict, materials: dict) -> list[str]:
    errors: list[str] = []
    for key in ("criteria", "indices", "parts", "profiles", "scenarios"):
        if key not in presets:
            errors.append(f"presets: missing '{key}'")
    if errors:
        return errors
    crit = [c["key"] for c in presets["criteria"]]
    if len(presets["parts"]) != 6:
        errors.append(f"presets: expected 6 parts, found {len(presets['parts'])}")
    if len(presets["profiles"]) != 5:
        errors.append(f"presets: expected 5 profiles, found {len(presets['profiles'])}")
    if len(presets["scenarios"]) != 3:
        errors.append(f"presets: expected 3 scenarios, found {len(presets['scenarios'])}")
    part_ids = {p["id"] for p in presets["parts"]}
    profile_ids = {p["id"] for p in presets["profiles"]}
    for p in presets["parts"]:
        for key in ("id", "name", "load_case", "performance_index", "constraints", "weights", "allowed_processes", "rationale"):
            if key not in p or p[key] in (None, "", [], {}):
                errors.append(f"part {p.get('id')}: missing '{key}'")
        if p.get("performance_index") not in presets["indices"]:
            errors.append(f"part {p.get('id')}: unknown performance index")
        if set(p.get("weights", {})) != set(crit):
            errors.append(f"part {p.get('id')}: weights must cover exactly {crit}")
        elif abs(sum(p["weights"].values()) - 1.0) > 1e-6:
            errors.append(f"part {p.get('id')}: default weights must sum to 1")
        bad = [x for x in p.get("allowed_processes", []) if x not in PROCESSES]
        if bad:
            errors.append(f"part {p.get('id')}: unknown processes {bad}")
    for pr in presets["profiles"]:
        if set(pr.get("modifiers", {})) != set(crit):
            errors.append(f"profile {pr.get('id')}: modifiers must cover exactly {crit}")
        elif any(v <= 0 for v in pr["modifiers"].values()):
            errors.append(f"profile {pr.get('id')}: modifiers must be positive")
    for s in presets["scenarios"]:
        if s.get("part") not in part_ids:
            errors.append(f"scenario {s.get('id')}: unknown part")
        if s.get("profile") not in profile_ids:
            errors.append(f"scenario {s.get('id')}: unknown profile")
    return errors


def main() -> int:
    mats = json.loads((ROOT / "data" / "materials.json").read_text())
    presets = json.loads((ROOT / "data" / "presets.json").read_text())
    errors = validate_materials(mats) + validate_presets(presets, mats)
    if errors:
        print("DATA VALIDATION FAILED")
        for e in errors:
            print(" -", e)
        return 1
    print(f"Data OK: {len(mats['materials'])} materials, {len(presets['parts'])} parts, "
          f"{len(presets['profiles'])} profiles, {len(presets['scenarios'])} scenarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
