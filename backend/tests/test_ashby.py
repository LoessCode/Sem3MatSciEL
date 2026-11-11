import math

import numpy as np

from airframeselect.ashby import INDICES, guide_line, index_ranges
from airframeselect.data import PROP_COL, all_materials


def val(ms, mid, prop, which="mid"):
    i = ms.index_of(mid)
    arr = {"mid": ms.mid, "lo": ms.lo, "hi": ms.hi}[which]
    return arr[i, PROP_COL[prop]]


def test_index_matches_direct_calculation():
    ms = all_materials()
    for index_id, (prop, a) in INDICES.items():
        lo, mid, hi = index_ranges(index_id, ms)
        for i in range(len(ms)):
            p = ms.mid[i, PROP_COL[prop]]
            rho = ms.mid[i, PROP_COL["density_kg_m3"]] / 1000.0
            assert math.isclose(mid[i], p**a / rho, rel_tol=1e-12)
            assert lo[i] <= mid[i] <= hi[i]


def test_range_propagation_is_interval_extremes():
    ms = all_materials()
    lo, _, hi = index_ranges("beam_stiffness", ms)
    i = ms.index_of("al6061")
    e_lo, e_hi = ms.lo[i, 1], ms.hi[i, 1]
    r_lo, r_hi = ms.lo[i, 0] / 1000, ms.hi[i, 0] / 1000
    assert math.isclose(lo[i], e_lo**0.5 / r_hi) and math.isclose(hi[i], e_hi**0.5 / r_lo)


def test_physically_robust_orderings_even_across_ranges():
    ms = all_materials()

    def rng(index_id, mid):
        lo, _, hi = index_ranges(index_id, ms)
        i = ms.index_of(mid)
        return lo[i], hi[i]

    # Carbon/epoxy beats Al 6061 and PLA on beam stiffness, even worst case vs best case.
    c_lo, _ = rng("beam_stiffness", "cfrp-qi")
    for other in ("al6061", "pla"):
        assert c_lo > rng("beam_stiffness", other)[1]
    # Wood-type materials beat steel and aluminium on beam stiffness.
    assert rng("beam_stiffness", "balsa")[0] > rng("beam_stiffness", "al6061")[1]
    assert rng("beam_stiffness", "al6061")[0] > rng("beam_stiffness", "ss304")[1]
    # Titanium beats Al 6061 on beam strength; carbon/epoxy beats stainless on tie strength.
    assert rng("beam_strength", "ti64")[0] > rng("beam_strength", "al6061")[1]
    assert rng("tie_strength", "cfrp-qi")[0] > rng("tie_strength", "ss304")[1]
    # Carbon/epoxy beats glass/epoxy on panel stiffness.
    assert rng("panel_stiffness", "cfrp-qi")[0] > rng("panel_stiffness", "gfrp-woven")[1]


def test_guide_line_slope_and_intercept():
    g = guide_line("beam_stiffness", "density_kg_m3", "youngs_modulus_GPa", 4.0)
    assert math.isclose(g["slope"], 2.0)
    # A point on the line: rho = 1600 kg/m3 -> E = (M * rho_Mg)^2 = (4*1.6)^2
    x = 1600.0
    y_line = 10 ** (g["slope"] * math.log10(x) + g["intercept"])
    assert math.isclose(y_line, (4.0 * 1.6) ** 2, rel_tol=1e-9)
    assert guide_line("beam_stiffness", "density_kg_m3", "tensile_strength_MPa", 4.0) is None
    assert guide_line("tie_strength", "cost_usd_per_kg", "tensile_strength_MPa", 4.0) is None
    assert math.isclose(guide_line("beam_strength", "density_kg_m3", "tensile_strength_MPa", 5.0)["slope"], 1.5)
