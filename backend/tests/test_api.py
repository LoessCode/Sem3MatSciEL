import csv
import io

import pytest
from fastapi.testclient import TestClient

from airframeselect.api import app

client = TestClient(app)
BASE = {"part": "arm", "profile": "balanced"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["materials"] == 47


def test_materials_and_presets():
    m = client.get("/api/materials").json()
    assert len(m["materials"]) == 47 and "disclaimer" in m
    p = client.get("/api/presets").json()
    assert len(p["parts"]) == 6 and len(p["profiles"]) == 5 and len(p["scenarios"]) == 3


def test_openapi_docs_enabled():
    assert client.get("/api/docs").status_code == 200
    spec = client.get("/api/openapi.json").json()
    assert "/api/rank" in spec["paths"] and "/api/export/pdf" in spec["paths"]


def test_cors_header_for_dev_origin():
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_rank_ok_and_constraint_override():
    r = client.post("/api/rank", json=BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["ranking"][0]["rank"] == 1 and body["excluded"]
    r2 = client.post("/api/rank", json={**BASE, "constraints": {"required_process": "fdm", "min_service_temp_C": None}})
    assert all("fdm" in x["processes"] for x in r2.json()["ranking"])
    assert r2.json()["inputs"]["constraints"]["min_service_temp_C"] is None


def test_rank_custom_weights_and_wsm():
    w = {"cost": 1, "performance_index": 1, "impact_resistance": 0, "max_service_temp": 0, "embodied_energy": 0, "recyclability": 0}
    r = client.post("/api/rank", json={**BASE, "weights": w, "method": "wsm"})
    assert r.status_code == 200 and r.json()["inputs"]["weights"]["cost"] == pytest.approx(0.5)


@pytest.mark.parametrize("payload", [
    {},                                                    # missing part
    {"part": "wing"},                                      # unknown part
    {**BASE, "profile": "mystery"},                        # unknown profile
    {**BASE, "method": "magic"},                           # bad enum
    {**BASE, "weights": {"cost": -1}},                     # negative weight
    {**BASE, "weights": {"speed": 1}},                     # unknown criterion
    {**BASE, "weights": {c: 0 for c in ["performance_index", "impact_resistance", "max_service_temp", "cost", "embodied_energy", "recyclability"]}},
    {**BASE, "constraints": {"max_density_kg_m3": -5}},    # negative limit
    {**BASE, "constraints": {"required_process": "forging"}},
    {**BASE, "constraints": {"colour": "red"}},            # unknown field
    {**BASE, "extra": 1},                                  # unknown top-level field
])
def test_rank_422(payload):
    r = client.post("/api/rank", json=payload)
    assert r.status_code == 422, r.text
    assert "detail" in r.json()


def test_rank_empty_result_is_200_with_message():
    r = client.post("/api/rank", json={**BASE, "constraints": {"max_density_kg_m3": 5}})
    assert r.status_code == 200 and r.json()["ranking"] == [] and r.json()["message"]


def test_robustness_ok_and_deterministic():
    req = {**BASE, "trials": 300, "seed": 3}
    a = client.post("/api/robustness", json=req).json()
    b = client.post("/api/robustness", json=req).json()
    assert a == b
    assert a["materials"][0]["confidence"] in {"High", "Medium", "Low"}


@pytest.mark.parametrize("extra", [{"trials": 5}, {"trials": 10**7}, {"concentration": -1}, {"range_scale": 3}, {"seed": -1}])
def test_robustness_422(extra):
    assert client.post("/api/robustness", json={**BASE, **extra}).status_code == 422


def test_robustness_fixed_weights_null_concentration():
    r = client.post("/api/robustness", json={**BASE, "trials": 200, "concentration": None, "range_scale": 0})
    assert r.status_code == 200
    assert r.json()["materials"][0]["p_rank1"] == 1.0


def test_compare():
    r = client.post("/api/compare", json={"material_ids": ["cfrp-qi", "al6061"], "part": "arm"})
    assert r.status_code == 200 and len(r.json()["materials"]) == 2


@pytest.mark.parametrize("payload", [
    {"material_ids": []},
    {"material_ids": ["pla", "petg", "abs", "asa"]},
    {"material_ids": ["nope"]},
    {"material_ids": ["pla", "pla"]},
    {"material_ids": ["pla"], "part": "wing"},
    {},
])
def test_compare_422(payload):
    assert client.post("/api/compare", json=payload).status_code == 422


def test_ashby():
    r = client.post("/api/ashby", json={**BASE, "axes": "density_vs_modulus", "top_n": 4})
    assert r.status_code == 200
    j = r.json()
    assert len(j["points"]) == 47 and j["guide"]["slope"] == pytest.approx(2.0) and len(j["top_ids"]) == 4


@pytest.mark.parametrize("extra", [{"axes": "bogus"}, {"top_n": -1}, {"top_n": 500}])
def test_ashby_422(extra):
    assert client.post("/api/ashby", json={**BASE, **extra}).status_code == 422


def test_export_csv():
    r = client.post("/api/export/csv", json={**BASE, "trials": 200})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert rows[1][0] == "rank" and rows[2][0] == "1" and len(rows) > 5
    header = rows[1]
    assert {"p_rank1", "p_top3", "confidence", "explanation"} <= set(header)


def test_export_pdf():
    r = client.post("/api/export/pdf", json={**BASE, "trials": 200})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and len(r.content) > 3000


def test_export_pdf_empty_ranking_still_works():
    r = client.post("/api/export/pdf", json={**BASE, "constraints": {"max_density_kg_m3": 5}})
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


@pytest.mark.parametrize("path", ["/api/export/csv", "/api/export/pdf"])
def test_export_422(path):
    assert client.post(path, json={"part": "wing"}).status_code == 422
    assert client.post(path, json={}).status_code == 422


def test_unknown_api_route_404_and_wrong_method_405():
    assert client.get("/api/nothing").status_code == 404
    assert client.get("/api/rank").status_code == 405
