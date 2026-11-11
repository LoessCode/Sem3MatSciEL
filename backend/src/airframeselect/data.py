"""Dataset loading and array views of the material database."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

# Raw property columns, in the order used by MaterialSet.lo / MaterialSet.hi.
PROPS = [
    "density_kg_m3",
    "youngs_modulus_GPa",
    "tensile_strength_MPa",
    "max_service_temp_C",
    "cost_usd_per_kg",
    "embodied_energy_MJ_per_kg",
]
PROP_COL = {p: i for i, p in enumerate(PROPS)}

# Decision criteria, in matrix column order.
CRITERIA = [
    "performance_index",
    "impact_resistance",
    "max_service_temp",
    "cost",
    "embodied_energy",
    "recyclability",
]
# True = benefit (higher is better), False = cost (lower is better).
BENEFIT = np.array([True, True, True, False, False, True])


def data_dir() -> Path:
    env = os.environ.get("AIRFRAMESELECT_DATA_DIR")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in list(here.parents) + [Path.cwd()]:
        cand = parent / "data"
        if (cand / "materials.json").is_file():
            return cand
    raise FileNotFoundError("Could not locate data/materials.json (set AIRFRAMESELECT_DATA_DIR)")


@lru_cache(maxsize=1)
def load_materials_doc() -> dict[str, Any]:
    return json.loads((data_dir() / "materials.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_presets() -> dict[str, Any]:
    return json.loads((data_dir() / "presets.json").read_text(encoding="utf-8"))


@dataclass
class MaterialSet:
    """Vectorised view of a list of material records."""

    records: list[dict[str, Any]]
    lo: np.ndarray = field(init=False)      # (n, 6) property minima
    hi: np.ndarray = field(init=False)      # (n, 6) property maxima
    impact: np.ndarray = field(init=False)  # (n,)
    recyc: np.ndarray = field(init=False)   # (n,)

    def __post_init__(self) -> None:
        n = len(self.records)
        self.lo = np.zeros((n, len(PROPS)))
        self.hi = np.zeros((n, len(PROPS)))
        self.impact = np.zeros(n)
        self.recyc = np.zeros(n)
        for i, r in enumerate(self.records):
            for j, p in enumerate(PROPS):
                self.lo[i, j] = r["properties"][p]["min"]
                self.hi[i, j] = r["properties"][p]["max"]
            self.impact[i] = r["scores"]["impact_resistance"]
            self.recyc[i] = r["scores"]["recyclability"]

    def __len__(self) -> int:
        return len(self.records)

    @property
    def mid(self) -> np.ndarray:
        return 0.5 * (self.lo + self.hi)

    @property
    def ids(self) -> list[str]:
        return [r["id"] for r in self.records]

    @property
    def names(self) -> list[str]:
        return [r["name"] for r in self.records]

    def subset(self, idx: list[int] | np.ndarray) -> "MaterialSet":
        return MaterialSet([self.records[int(i)] for i in idx])

    def index_of(self, material_id: str) -> int:
        for i, r in enumerate(self.records):
            if r["id"] == material_id:
                return i
        raise KeyError(material_id)


def all_materials() -> MaterialSet:
    return MaterialSet(list(load_materials_doc()["materials"]))


def get_part(part_id: str) -> dict[str, Any]:
    for p in load_presets()["parts"]:
        if p["id"] == part_id:
            return p
    raise KeyError(f"unknown part '{part_id}'")


def get_profile(profile_id: str) -> dict[str, Any]:
    for p in load_presets()["profiles"]:
        if p["id"] == profile_id:
            return p
    raise KeyError(f"unknown profile '{profile_id}'")
