import pytest

from airframeselect.pipeline import InputError, resolve_inputs, run_ashby, run_compare, run_ranking


def test_default_ranking_basics():
    r = run_ranking("arm", "balanced")
    assert r["n_candidates"] + len(r["excluded"]) == r["n_total"]
    ranks = [x["rank"] for x in r["ranking"]]
    assert ranks == list(range(1, len(ranks) + 1))
    scores = [x["score"] for x in r["ranking"]]
    assert scores == sorted(scores, reverse=True)
    assert abs(sum(r["inputs"]["weights"].values()) - 1) < 1e-12
    for row in r["ranking"]:
        assert abs(sum(row["contributions"].values()) - row["wsm_score"]) < 1e-9
        assert row["explanation"]


def test_every_excluded_material_has_a_reason():
    r = run_ranking("arm", "balanced")
    assert r["excluded"]
    assert all(e["reasons"] and all(isinstance(t, str) and len(t) > 10 for t in e["reasons"]) for e in r["excluded"])
    foam = next(e for e in r["excluded"] if e["id"] == "epp")
    assert any("weak" in t for t in foam["reasons"])


def test_constraints_actually_filter():
    r = run_ranking("arm", "balanced", constraints={"max_density_kg_m3": 1300})
    assert all(x["values"]["density_kg_m3"] <= 1300 for x in r["ranking"])
    r = run_ranking("arm", "balanced", constraints={"required_process": "fdm"})
    assert all("fdm" in x["processes"] for x in r["ranking"])
    ex = {e["id"]: e for e in r["excluded"]}
    assert any("required process" in t for t in ex["al6061"]["reasons"])
    r = run_ranking("arm", "balanced", constraints={"min_service_temp_C": 200})
    assert {x["id"] for x in r["ranking"]} <= {"peek", "pei", "peek-cf", "ti64", "ss304", "aerogel-panel"}


def test_null_constraint_removes_limit():
    tight = run_ranking("arm", "balanced")
    loose = run_ranking("arm", "balanced", constraints={"min_strength_MPa": None, "min_service_temp_C": None})
    assert loose["n_candidates"] > tight["n_candidates"]


def test_no_feasible_materials_gives_message_not_error():
    r = run_ranking("arm", "balanced", constraints={"max_density_kg_m3": 5})
    assert r["ranking"] == [] and r["message"] and len(r["excluded"]) == r["n_total"]


def test_profile_modifiers_documented_effect():
    bal = resolve_inputs("arm", "balanced")["weights"]
    eco = resolve_inputs("arm", "eco")["weights"]
    assert eco["embodied_energy"] > bal["embodied_energy"]
    assert eco["performance_index"] < bal["performance_index"]
    assert abs(sum(eco.values()) - 1) < 1e-12


def test_explicit_weights_override_and_normalise():
    w = resolve_inputs("arm", "balanced", weights={"cost": 10, "performance_index": 10, "impact_resistance": 0,
                                                  "max_service_temp": 0, "embodied_energy": 0, "recyclability": 0})["weights"]
    assert w["cost"] == pytest.approx(0.5) and w["impact_resistance"] == 0


def test_input_errors():
    with pytest.raises(InputError):
        resolve_inputs("wing")
    with pytest.raises(InputError):
        resolve_inputs("arm", "mystery")
    with pytest.raises(InputError):
        resolve_inputs("arm", weights={"speed": 1})
    with pytest.raises(InputError):
        resolve_inputs("arm", weights={"cost": -1})
    with pytest.raises(InputError):
        resolve_inputs("arm", weights={k: 0 for k in ["performance_index", "impact_resistance", "max_service_temp",
                                                        "cost", "embodied_energy", "recyclability"]})
    with pytest.raises(InputError):
        resolve_inputs("arm", constraints={"required_process": "forging"})
    with pytest.raises(InputError):
        resolve_inputs("arm", constraints={"max_cost_usd_per_kg": -5})
    with pytest.raises(InputError):
        resolve_inputs("arm", method="magic")


def test_methods_select_ordering():
    t = run_ranking("arm", "balanced", method="topsis")
    w = run_ranking("arm", "balanced", method="wsm")
    assert t["ranking"][0]["topsis_score"] == t["ranking"][0]["score"]
    assert w["ranking"][0]["wsm_score"] == w["ranking"][0]["score"]
    assert {"top1_agree", "top3_agree", "spearman", "top3_overlap"} <= set(t["agreement"])


def test_explanation_sentence_style():
    r = run_ranking("arm", "balanced")
    s = r["ranking"][0]["explanation"]
    assert s.endswith(".") and "ranks first mainly because of its" in s


def test_compare():
    c = run_compare(["cfrp-qi", "al6061", "pla"], "arm")
    assert len(c["materials"]) == 3
    for m in c["materials"]:
        assert all(0 <= v <= 1 for v in m["normalized"].values())
    perf = {m["id"]: m["normalized"]["performance_index"] for m in c["materials"]}
    assert perf["cfrp-qi"] > perf["al6061"] > perf["pla"]
    with pytest.raises(InputError):
        run_compare(["a", "b", "c", "d"])
    with pytest.raises(InputError):
        run_compare(["nope"])
    with pytest.raises(InputError):
        run_compare(["pla", "pla"])


def test_ashby_chart_data():
    a = run_ashby("arm", "balanced", axes="density_vs_modulus", top_n=3)
    assert len(a["points"]) == 47
    assert sum(p["top"] for p in a["points"]) == 3
    assert a["guide"] and a["guide"]["slope"] == pytest.approx(2.0)
    assert all(p["x"]["min"] <= p["x"]["max"] for p in a["points"])
    b = run_ashby("arm", "balanced", axes="density_vs_strength")
    assert b["guide"] is None
    c = run_ashby("arm", "balanced", axes="cost_vs_strength")
    assert c["x"]["property"] == "cost_usd_per_kg"
    with pytest.raises(InputError):
        run_ashby("arm", axes="bogus")
