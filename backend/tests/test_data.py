import copy
import json
from pathlib import Path

import validate_data as vd

ROOT = Path(__file__).resolve().parents[2]


def load():
    mats = json.loads((ROOT / "data" / "materials.json").read_text())
    presets = json.loads((ROOT / "data" / "presets.json").read_text())
    return mats, presets


def test_shipped_data_passes_validator():
    mats, presets = load()
    assert vd.validate_materials(mats) == []
    assert vd.validate_presets(presets, mats) == []


def test_every_record_flagged_for_verification():
    mats, _ = load()
    assert all(m["data_status"] == "typical-value-needs-verification" for m in mats["materials"])


def test_required_families_and_names_present():
    mats, _ = load()
    names = " ".join(m["name"].lower() for m in mats["materials"])
    for needle in ["pla", "petg", "abs", "asa", "pa12", "tpu", "polycarbonate", "peek", "pla-cf", "petg-cf",
                   "pa-cf", "pa-gf", "carbon/epoxy", "glass/epoxy", "aramid/epoxy", "basalt/epoxy", "flax/epoxy",
                   "hemp-pla", "6061", "7075", "ti-6al-4v", "az31", "304", "balsa", "plywood", "cork", "epp", "eps",
                   "pet structural foam", "honeycomb", "aerogel", "recycled pet", "recycled nylon"]:
        assert needle in names, needle
    assert {m["family"] for m in mats["materials"]} == vd.FAMILIES


def test_validator_catches_problems():
    mats, _ = load()
    bad = copy.deepcopy(mats)
    bad["materials"][0]["properties"]["density_kg_m3"] = {"min": 2000, "max": 1000}
    assert any("min > max" in e for e in vd.validate_materials(bad))
    bad = copy.deepcopy(mats)
    bad["materials"][0]["properties"]["density_kg_m3"] = {"min": 5000, "max": 6000}
    assert any("plausibility" in e for e in vd.validate_materials(bad))
    bad = copy.deepcopy(mats)
    del bad["materials"][1]["notes"]
    assert any("missing field 'notes'" in e for e in vd.validate_materials(bad))
    bad = copy.deepcopy(mats)
    bad["materials"][2]["scores"]["recyclability"] = 9
    assert any("score" in e for e in vd.validate_materials(bad))
    bad = copy.deepcopy(mats)
    bad["materials"][3]["processes"] = ["magic"]
    assert any("unknown processes" in e for e in vd.validate_materials(bad))


def test_preset_weights_and_profiles():
    _, presets = load()
    assert len(presets["parts"]) == 6 and len(presets["profiles"]) == 5
    assert {p["id"] for p in presets["profiles"]} == {"balanced", "endurance", "impact-tolerant", "budget", "eco"}
