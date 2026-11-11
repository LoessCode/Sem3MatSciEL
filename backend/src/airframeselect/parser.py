"""Rule-based (non-LLM) parser that turns a plain-English requirement into form inputs.

It only recognises a fixed vocabulary and numbers next to units; every rule that fires is
reported back so the user can see exactly why a field was filled.
"""
from __future__ import annotations

import re
from typing import Any

PART_RULES: list[tuple[str, str]] = [
    (r"\b(arm|arms|boom|booms)\b", "arm"),
    (r"\b(prop|props|propeller|propellers|blade|blades|rotor)\b", "propeller"),
    (r"\b(landing gear|landing leg|landing legs|skid|skids|undercarriage)\b", "landing_gear"),
    (r"\b(battery|batteries|enclosure|housing|case|box|canopy)\b", "battery_enclosure"),
    (r"\b(fuselage|skin|shell|wing skin|body)\b", "fuselage_skin"),
    (r"\b(plate|plates|frame|chassis|deck|bottom plate|top plate)\b", "plate"),
]
PROFILE_RULES: list[tuple[str, str]] = [
    (r"\b(endurance|long[- ]range|long[- ]flight|lightweight|light[- ]weight|as light as|minimi[sz]e weight)\b", "endurance"),
    (r"\b(crash|crashes|crash[- ]prone|impact|tough|durable|fpv|racing|race|rugged|survive|survives)\b", "impact-tolerant"),
    (r"\b(cheap|cheapest|budget|low[- ]cost|inexpensive|affordable)\b", "budget"),
    (r"\b(eco|eco[- ]friendly|green|sustainable|recycl\w*|environment\w*|low carbon)\b", "eco"),
]
PROCESS_RULES: list[tuple[str, str]] = [
    (r"\b(3d[- ]?print\w*|fdm|printable|printed|print)\b", "fdm"),
    (r"\b(cnc|laser[- ]cut|router|routed|cut from sheet)\b", "cnc-cut"),
    (r"\b(machin\w+)\b", "machining"),
    (r"\b(injection[- ]mould\w*|injection[- ]mold\w*|moulded|molded)\b", "injection"),
    (r"\b(layup|lay-up|hand layup|prepreg|vacuum bag\w*|wet layup)\b", "layup"),
    (r"\b(sheet[- ]metal|bent|folded|thermoform\w*)\b", "sheet-forming"),
]
NUM = r"(\d+(?:[.,]\d+)?)"


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def _first(rules: list[tuple[str, str]], text: str) -> tuple[str, str] | None:
    """Return (value, matched text) for the earliest match in the text across rules."""
    best: tuple[int, str, str] | None = None
    for pattern, value in rules:
        m = re.search(pattern, text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), value, m.group(0))
    return (best[1], best[2]) if best else None


def parse_requirement(text: str) -> dict[str, Any]:
    t = " " + text.lower().strip() + " "
    matches: list[dict[str, str]] = []
    out: dict[str, Any] = {"part": None, "profile": None, "constraints": {}, "matches": matches, "notes": []}
    if not t.strip():
        out["notes"].append("Type a short description, for example: 'a light 3D printed arm for a crash-prone racing quad'.")
        return out
    # Part rules are tried in a fixed priority so 'battery box' is not mistaken for a generic 'box'.
    part = _first(PART_RULES, t)
    if part:
        out["part"] = part[0]
        matches.append({"field": "part", "value": part[0], "because": f'found "{part[1]}"'})
    # Profile: all matched keyword groups are reported; first match wins.
    prof = _first(PROFILE_RULES, t)
    if prof:
        out["profile"] = prof[0]
        matches.append({"field": "profile", "value": prof[0], "because": f'found "{prof[1]}"'})
    proc = _first(PROCESS_RULES, t)
    if proc:
        out["constraints"]["required_process"] = proc[0]
        matches.append({"field": "required_process", "value": proc[0], "because": f'found "{proc[1]}"'})
    # Numeric limits (value next to a unit and a direction word).
    m = re.search(rf"(?:under|below|less than|at most|max(?:imum)?|cheaper than|up to|<)\s*\$?\s*{NUM}\s*(?:usd|dollars?|\$)?\s*(?:/|per)\s*kg", t) \
        or re.search(rf"\$\s*{NUM}\s*(?:/|per)\s*kg\s*(?:or less|max|maximum)?", t)
    if m:
        out["constraints"]["max_cost_usd_per_kg"] = _num(m.group(1))
        matches.append({"field": "max_cost_usd_per_kg", "value": _num(m.group(1)), "because": f'found "{m.group(0).strip()}"'})
    m = re.search(rf"(?:withstand|survive|survives|tolerate|rated for|up to|at least|above|over|resist)\s*{NUM}\s*(?:°\s*c|deg(?:rees)?\s*c?|celsius|c\b)", t) \
        or re.search(rf"{NUM}\s*(?:°\s*c|degrees?\s*c(?:elsius)?|celsius)", t)
    if m:
        out["constraints"]["min_service_temp_C"] = _num(m.group(1))
        matches.append({"field": "min_service_temp_C", "value": _num(m.group(1)), "because": f'found "{m.group(0).strip()}"'})
    elif re.search(r"\b(hot|summer|sun|sunlit|desert|warm motors?)\b", t):
        out["constraints"]["min_service_temp_C"] = 70.0
        matches.append({"field": "min_service_temp_C", "value": 70.0, "because": "heat-related word found; 70 C assumed"})
    m = re.search(rf"(?:density\s*(?:under|below|less than|<)|lighter than|less than|under|below)\s*{NUM}\s*(?:kg/m3|kg/m\^3|kg per m3|kg/m³)", t)
    if m:
        out["constraints"]["max_density_kg_m3"] = _num(m.group(1))
        matches.append({"field": "max_density_kg_m3", "value": _num(m.group(1)), "because": f'found "{m.group(0).strip()}"'})
    m = re.search(rf"(?:at least|over|above|min(?:imum)?|stronger than|>)\s*{NUM}\s*mpa", t)
    if m:
        out["constraints"]["min_strength_MPa"] = _num(m.group(1))
        matches.append({"field": "min_strength_MPa", "value": _num(m.group(1)), "because": f'found "{m.group(0).strip()}"'})
    if not matches:
        out["notes"].append("No known keywords were found. Try naming a part (arm, plate, propeller, landing gear, battery enclosure, fuselage skin) and a goal such as light, tough, cheap or eco-friendly.")
    elif out["part"] is None:
        out["notes"].append("No part was recognised, so the current part is kept.")
    return out
