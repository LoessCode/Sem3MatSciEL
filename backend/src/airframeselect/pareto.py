"""Pareto-front analysis over two criteria of the feasible candidates."""
from __future__ import annotations

import numpy as np

from .data import BENEFIT, CRITERIA


def pareto_front(X: np.ndarray, columns: list[int]) -> tuple[np.ndarray, list[int | None]]:
    """Return (is_front, dominated_by) for matrix X restricted to `columns`.

    A row is dominated if another row is at least as good on every chosen criterion
    (respecting benefit/cost direction) and strictly better on at least one.
    dominated_by gives the index of one dominating row (the one with the best summed margin) or None.
    """
    sign = np.where(BENEFIT[columns], 1.0, -1.0)
    Y = X[:, columns] * sign  # larger is always better
    n = len(Y)
    front = np.ones(n, dtype=bool)
    dom: list[int | None] = [None] * n
    for i in range(n):
        ge = np.all(Y >= Y[i], axis=1)
        gt = np.any(Y > Y[i], axis=1)
        dominators = np.where(ge & gt)[0]
        if len(dominators):
            front[i] = False
            best = dominators[np.argmax((Y[dominators] - Y[i]).sum(axis=1))]
            dom[i] = int(best)
    return front, dom


def criteria_columns(keys: list[str]) -> list[int]:
    return [CRITERIA.index(k) for k in keys]
