#!/usr/bin/env python3
"""Regenerate docs/DATA_VERIFICATION.md from data/materials.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
doc = json.loads((ROOT / "data" / "materials.json").read_text(encoding="utf-8"))
SHORT = [
    ("density_kg_m3", "Density kg/m3"),
    ("youngs_modulus_GPa", "E GPa"),
    ("tensile_strength_MPa", "Strength MPa"),
    ("max_service_temp_C", "Tmax C"),
    ("cost_usd_per_kg", "Cost $/kg"),
    ("embodied_energy_MJ_per_kg", "Emb. energy MJ/kg"),
]


def g(x: float) -> str:
    return f"{x:g}"


lines = [
    "# Data verification checklist", "",
    "**Every value in `data/materials.json` is a typical figure from general engineering knowledge, given as a min-max range, and every record carries the status `typical-value-needs-verification`.**",
    "Before the project is submitted or any result is relied on, spot-check the values below against supplier datasheets or an engineering handbook (cite the source you actually used in your report), tick the box, and note the source in the last column.", "",
    "How to use this file:", "",
    "1. Pick the highest-impact materials first: the top-ranked materials in your demo scenarios and the ones you intend to defend.",
    "2. For each property, check that the stated range brackets the datasheet value for the grade and process you mean (for example XY-printed filament, quasi-isotropic laminate at about 50% fibre volume).",
    "3. If a value is wrong, edit `data/materials.json`, run `python scripts/validate_data.py` and `make test`, and re-run `python scripts/make_validation_report.py`.",
    "4. Change `data_status` to a verified status only for records you have fully checked, and extend the validator accordingly.", "",
    "Scores (impact resistance, recyclability) are 1-5 judgement values; review them with your instructor rather than a datasheet.", "",
    "Legend: `[ ]` = not yet verified. Ranges are shown as min-max.", "",
]
header = "| Material (id) | Family | " + " | ".join(h for _, h in SHORT) + " | Impact 1-5 | Recycl. 1-5 | Source / notes |"
lines += [header, "|" + "---|" * (len(SHORT) + 5)]
for m in doc["materials"]:
    cells = []
    for k, _ in SHORT:
        p = m["properties"][k]
        cells.append(f"{g(p['min'])}-{g(p['max'])} [ ]")
    s = m["scores"]
    lines.append(
        f"| {m['name']} (`{m['id']}`) | {m['family']} | " + " | ".join(cells)
        + f" | {s['impact_resistance']} [ ] | {s['recyclability']} [ ] |  |"
    )
lines += ["", "## Property basis per record", "", "| Material | Basis stated in the data |", "|---|---|"]
for m in doc["materials"]:
    lines.append(f"| {m['name']} | {m['property_basis']} |")
lines.append("")
(ROOT / "docs" / "DATA_VERIFICATION.md").write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote docs/DATA_VERIFICATION.md for {len(doc['materials'])} materials")
