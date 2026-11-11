import time

import numpy as np
import pytest

from airframeselect.data import CRITERIA, MaterialSet, all_materials
from airframeselect.pipeline import run_ranking, run_robustness
from airframeselect.robustness import confidence_label, run_monte_carlo

W = np.array([0.35, 0.20, 0.10, 0.15, 0.10, 0.10])


def kept_set():
    r = run_ranking("arm", "balanced")
    ms = all_materials()
    return ms.subset([ms.index_of(x["id"]) for x in r["ranking"]]), r


def test_deterministic_under_fixed_seed():
    ms, _ = kept_set()
    a = run_monte_carlo(ms, "beam_stiffness", W, seed=7, trials=500)
    b = run_monte_carlo(ms, "beam_stiffness", W, seed=7, trials=500)
    c = run_monte_carlo(ms, "beam_stiffness", W, seed=8, trials=500)
    np.testing.assert_array_equal(a["rank_distribution"], b["rank_distribution"])
    assert not np.array_equal(a["rank_distribution"], c["rank_distribution"])


def test_rank_probabilities_sum_to_one():
    ms, _ = kept_set()
    mc = run_monte_carlo(ms, "beam_stiffness", W, trials=400)
    d = mc["rank_distribution"]
    np.testing.assert_allclose(d.sum(axis=0), 1.0)  # each rank is taken by exactly one material
    np.testing.assert_allclose(d.sum(axis=1), 1.0)  # each material takes exactly one rank
    np.testing.assert_allclose(mc["p_rank1"].sum(), 1.0)
    assert np.all(mc["p_top3"] >= mc["p_rank1"] - 1e-12)


@pytest.mark.parametrize("method", ["topsis", "wsm"])
def test_collapsed_ranges_and_fixed_weights_give_certain_winner(method):
    ms, _ = kept_set()
    mc = run_monte_carlo(ms, "beam_stiffness", W, method=method, trials=200, concentration=None, range_scale=0.0)
    winner = int(np.argmin(mc["baseline_ranks"]))
    assert mc["p_rank1"][winner] == 1.0
    assert mc["p_rank1"].sum() == 1.0
    assert all(c == "High" for c in mc["confidence"])


def test_collapsed_ranges_in_data_also_certain():
    # Same property via the data itself: min == max for every property.
    ms, _ = kept_set()
    recs = []
    for r in ms.records:
        mid = {k: 0.5 * (v["min"] + v["max"]) for k, v in r["properties"].items()}
        recs.append({**r, "properties": {k: {"min": m, "max": m} for k, m in mid.items()}})
    flat = MaterialSet(recs)
    mc = run_monte_carlo(flat, "beam_stiffness", W, trials=100, concentration=None)
    assert mc["p_rank1"].max() == 1.0


def test_performance_under_three_seconds_for_60_materials():
    ms = all_materials()
    recs = list(ms.records) + [dict(r, id=r["id"] + "-x") for r in ms.records[:13]]
    big = MaterialSet(recs)
    assert len(big) == 60
    t = time.perf_counter()
    run_monte_carlo(big, "beam_stiffness", W, trials=2000)
    assert time.perf_counter() - t < 3.0


def test_confidence_thresholds():
    assert confidence_label(0.9) == "High" and confidence_label(0.75) == "High"
    assert confidence_label(0.5) == "Medium" and confidence_label(0.40) == "Medium"
    assert confidence_label(0.1) == "Low"


def test_higher_concentration_means_less_weight_noise():
    ms, _ = kept_set()
    loose = run_monte_carlo(ms, "beam_stiffness", W, trials=1000, concentration=2, range_scale=0.0)
    tight = run_monte_carlo(ms, "beam_stiffness", W, trials=1000, concentration=2000, range_scale=0.0)
    assert tight["p_rank1"].max() > loose["p_rank1"].max()


def test_invalid_settings():
    ms, _ = kept_set()
    with pytest.raises(ValueError):
        run_monte_carlo(ms, "beam_stiffness", W, trials=0)
    with pytest.raises(ValueError):
        run_monte_carlo(ms, "beam_stiffness", W, concentration=-1)
    with pytest.raises(ValueError):
        run_monte_carlo(ms, "beam_stiffness", W, range_scale=2)


def test_pipeline_robustness_shape():
    out = run_robustness("arm", "balanced", trials=300)
    assert out["settings"]["trials"] == 300
    assert len(out["materials"]) == out["n_candidates"]
    first = out["materials"][0]
    assert first["baseline_rank"] == 1
    assert abs(sum(first["rank_distribution"]) - 1) < 1e-9
    assert first["confidence"] in {"High", "Medium", "Low"}
    assert out["winner"]["baseline_top_id"] == first["id"]
    assert CRITERIA  # criteria constant exists
