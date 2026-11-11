import numpy as np
import pytest
from fastapi.testclient import TestClient

from airframeselect.api import app
from airframeselect.data import BENEFIT
from airframeselect.parser import parse_requirement
from airframeselect.pareto import pareto_front
from airframeselect.pipeline import InputError, run_pareto

client = TestClient(app)


def test_pareto_front_by_hand():
    # columns: performance (benefit), impact (benefit), temp (benefit), cost (cost)
    X = np.array([
        [5.0, 1, 1, 10.0, 1, 1],   # 0: best performance, expensive
        [4.0, 1, 1, 2.0, 1, 1],    # 1: cheaper, slightly less performance -> front
        [3.0, 1, 1, 5.0, 1, 1],    # 2: dominated by 1 (worse on both)
        [1.0, 1, 1, 1.0, 1, 1],    # 3: cheapest -> front
    ])
    front, dom = pareto_front(X, [0, 3])
    assert list(front) == [True, True, False, True]
    assert dom[2] == 1 and dom[0] is None
    assert BENEFIT[0] and not BENEFIT[3]


def test_pareto_no_dominated_member_is_flagged_front_and_every_other_has_dominator():
    r = run_pareto("arm", "balanced")
    pts = r["points"]
    assert any(p["pareto"] for p in pts) and r["front_ids"]
    for p in pts:
        if not p["pareto"]:
            assert p["dominated_by"]
    # direction check: front members are not dominated (cost lower is better, performance higher)
    for a in pts:
        if a["pareto"]:
            assert not any(b["x"] <= a["x"] and b["y"] >= a["y"] and (b["x"] < a["x"] or b["y"] > a["y"]) for b in pts)


def test_pareto_errors_and_api():
    with pytest.raises(InputError):
        run_pareto("arm", x_criterion="cost", y_criterion="cost")
    with pytest.raises(InputError):
        run_pareto("arm", x_criterion="nope")
    assert client.post("/api/pareto", json={"part": "arm", "x_criterion": "bogus"}).status_code == 422
    assert client.post("/api/pareto", json={"part": "wing"}).status_code == 422
    r = client.post("/api/pareto", json={"part": "arm", "x_criterion": "embodied_energy", "y_criterion": "impact_resistance"})
    assert r.status_code == 200 and r.json()["front_ids"]
    r = client.post("/api/pareto", json={"part": "arm", "constraints": {"max_density_kg_m3": 5}})
    assert r.status_code == 200 and r.json()["points"] == []


def test_parser_examples():
    r = parse_requirement("A cheap 3D printed battery box that survives 70 C")
    assert r["part"] == "battery_enclosure" and r["profile"] == "budget"
    assert r["constraints"] == {"required_process": "fdm", "min_service_temp_C": 70.0}
    r = parse_requirement("light crash-prone racing quad arm under $40/kg")
    assert r["part"] == "arm" and r["profile"] == "impact-tolerant" and r["constraints"]["max_cost_usd_per_kg"] == 40.0
    r = parse_requirement("eco-friendly fuselage skin, density below 1500 kg/m3, at least 80 MPa")
    assert r["constraints"] == {"max_density_kg_m3": 1500.0, "min_strength_MPa": 80.0}
    assert all("because" in m for m in r["matches"])


def test_parser_unknown_and_empty():
    assert parse_requirement("zzz")["notes"] and parse_requirement("zzz")["part"] is None
    assert parse_requirement("   ")["notes"]


def test_parse_api():
    r = client.post("/api/parse", json={"text": "propeller for hot weather"})
    assert r.status_code == 200 and r.json()["part"] == "propeller"
    assert r.json()["constraints"]["min_service_temp_C"] == 70.0
    assert client.post("/api/parse", json={}).status_code == 422
    assert client.post("/api/parse", json={"text": "x" * 2000}).status_code == 422
