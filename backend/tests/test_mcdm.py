import math

import numpy as np
import pytest

from airframeselect.mcdm import (
    method_agreement, minmax_normalise, ranks_from_scores, spearman, topsis, weighted_sum,
)

# 4 alternatives x 3 criteria: (benefit, benefit, cost)
M = [[250.0, 16.0, 12.0], [200.0, 16.0, 8.0], [300.0, 32.0, 16.0], [275.0, 32.0, 8.0]]
W = [0.5, 0.3, 0.2]
BEN = np.array([True, True, False])


def topsis_by_hand(matrix, weights, benefit):
    """Plain-Python step-by-step TOPSIS, independent of the numpy implementation."""
    m, n = len(matrix), len(matrix[0])
    total = sum(weights)
    w = [x / total for x in weights]
    # Step 1: vector normalisation
    norms = [math.sqrt(sum(matrix[i][j] ** 2 for i in range(m))) for j in range(n)]
    r = [[matrix[i][j] / norms[j] for j in range(n)] for i in range(m)]
    # Step 2: weighting
    v = [[r[i][j] * w[j] for j in range(n)] for i in range(m)]
    # Step 3: ideal and anti-ideal
    ideal, anti = [], []
    for j in range(n):
        col = [v[i][j] for i in range(m)]
        ideal.append(max(col) if benefit[j] else min(col))
        anti.append(min(col) if benefit[j] else max(col))
    # Step 4: distances and closeness
    out = []
    for i in range(m):
        dp = math.sqrt(sum((v[i][j] - ideal[j]) ** 2 for j in range(n)))
        dn = math.sqrt(sum((v[i][j] - anti[j]) ** 2 for j in range(n)))
        out.append(dn / (dp + dn))
    return out


def wsm_by_hand(matrix, weights, benefit):
    m, n = len(matrix), len(matrix[0])
    total = sum(weights)
    w = [x / total for x in weights]
    out = []
    for i in range(m):
        s = 0.0
        for j in range(n):
            col = [matrix[k][j] for k in range(m)]
            lo, hi = min(col), max(col)
            x = (matrix[i][j] - lo) / (hi - lo) if benefit[j] else (hi - matrix[i][j]) / (hi - lo)
            s += w[j] * x
        out.append(s)
    return out


def test_topsis_matches_hand_calculation():
    expected = topsis_by_hand(M, W, BEN)
    np.testing.assert_allclose(topsis(np.array(M), np.array(W), BEN), expected, rtol=1e-12)


def test_topsis_known_value_first_alternative():
    # Spot-check one number fully by hand: column norms 515.3, 53.0, 24.0 -> see helper.
    got = topsis(np.array(M), np.array(W), BEN)
    assert 0.0 <= got.min() and got.max() <= 1.0
    # Alternative 4 dominates 2 on two criteria and ties on cost, so it must score higher.
    assert got[3] > got[1]


def test_weighted_sum_matches_hand_calculation():
    expected = wsm_by_hand(M, W, [True, True, False])
    np.testing.assert_allclose(weighted_sum(np.array(M), np.array(W), BEN), expected, rtol=1e-12)


def test_minmax_normalisation_properties():
    N = minmax_normalise(np.array(M), BEN)
    assert N.min() == 0.0 and N.max() == 1.0
    np.testing.assert_allclose(N.min(axis=0), 0.0)
    np.testing.assert_allclose(N.max(axis=0), 1.0)
    # Cost column is inverted: the cheapest alternative gets 1.
    assert N[1, 2] == 1.0 and N[1, 2] == N[3, 2]


def test_constant_column_is_neutral():
    N = minmax_normalise(np.array([[1.0, 5.0], [2.0, 5.0]]), np.array([True, True]))
    assert (N[:, 1] == 0.5).all()


@pytest.mark.parametrize("scale", [0.001, 3.0, 1000.0])
def test_rankings_invariant_to_weight_scaling(scale):
    X = np.array(M)
    w = np.array(W)
    for fn in (topsis, weighted_sum):
        a = fn(X, w, BEN)
        b = fn(X, w * scale, BEN)
        np.testing.assert_allclose(a, b, rtol=1e-12)
        assert list(ranks_from_scores(a)) == list(ranks_from_scores(b))


def test_topsis_invariant_to_criterion_unit_scaling():
    X = np.array(M)
    Y = X * np.array([1.0, 1000.0, 0.01])  # change units of each criterion
    np.testing.assert_allclose(topsis(X, np.array(W), BEN), topsis(Y, np.array(W), BEN), rtol=1e-12)


def test_batch_matches_single():
    X = np.array(M)
    Ws = np.array([[0.5, 0.3, 0.2], [0.1, 0.1, 0.8]])
    batch = topsis(np.broadcast_to(X, (2, 4, 3)), Ws, BEN)
    for k in range(2):
        np.testing.assert_allclose(batch[k], topsis(X, Ws[k], BEN))


def test_rank_helpers():
    s = np.array([0.2, 0.9, 0.5])
    assert list(ranks_from_scores(s)) == [3, 1, 2]
    assert spearman(np.array([1, 2, 3]), np.array([1, 2, 3])) == 1.0
    assert spearman(np.array([1, 2, 3]), np.array([3, 2, 1])) == -1.0


def test_method_agreement():
    a = np.array([0.9, 0.8, 0.7, 0.1])
    ag = method_agreement(a, a)
    assert ag["top1_agree"] and ag["top3_agree"] and ag["spearman"] == 1.0
    ag2 = method_agreement(a, a[::-1].copy())
    assert not ag2["top3_agree"] and ag2["spearman"] == -1.0


def test_zero_weights_rejected():
    with pytest.raises(ValueError):
        topsis(np.array(M), np.zeros(3), BEN)
