# Methodology

This document describes exactly what the code in `backend/src/airframeselect/` computes. Section numbers match the Methodology page in the app.

## 0. Pipeline

```
part + mission profile + limits + weights
  -> hard-constraint filter (constraints.py)          removes materials, with reasons
  -> Ashby performance index from midpoints (ashby.py)
  -> 6-criterion decision matrix (robustness.criteria_from_raw)
  -> TOPSIS and weighted sum (mcdm.py)                 both always computed; one is the primary ranking
  -> Monte Carlo robustness (robustness.py)            weight and data uncertainty
  -> explanations (explain.py), comparison (compare.py), Ashby chart data, Pareto front (pareto.py)
```

## 1. Ashby performance indices

Units follow the usual Ashby convention: E in GPa, strength sigma in MPa, density rho in Mg/m3 (kg/m3 divided by 1000). Rankings do not depend on the unit choice because every criterion is normalised before use.

| Index id | Formula | Load case |
|---|---|---|
| `beam_stiffness` | E^(1/2) / rho | beam that must not bend too far (arm) |
| `beam_strength` | sigma^(2/3) / rho | beam that must not break (propeller, landing gear) |
| `panel_stiffness` | E^(1/3) / rho | flat panel limited by stiffness or buckling (frame plate, fuselage skin) |
| `panel_strength` | sigma^(1/2) / rho | flat panel limited by strength (battery enclosure) |
| `tie_stiffness` | E / rho | tension member limited by stretch |
| `tie_strength` | sigma / rho | tension member limited by strength |

- **Value** is computed from the midpoint of each property range.
- **Range propagation** uses interval arithmetic: the minimum pairs the lowest property value with the highest density, the maximum the highest property with the lowest density.
- **Guide line.** For M = P^a / rho_Mg, a line of constant M on a log-log chart of P against density has slope 1/a. With density plotted in kg/m3 the intercept is (log10(M) - 3)/a. The app draws the line through the top-ranked material and shows it only when the chart's y axis matches the index property (density vs modulus for stiffness indices, density vs strength for strength indices).

Part to index assignment is in `data/presets.json` and each part carries a plain-language rationale.

## 2. Hard-constraint filter

Limits: maximum density, minimum strength, minimum service temperature, maximum cost, required process. Each limit is tested against the **midpoint** of the property. If a process is required the material must list it; otherwise the material must list at least one process that the part allows. Every excluded material receives one reason sentence per violated limit. The surviving set is fixed for the rest of the analysis (including Monte Carlo). A `null` limit means "no limit".

## 3. Criteria

| Criterion | Direction | Source |
|---|---|---|
| performance_index | benefit | Ashby index of the part |
| impact_resistance | benefit | score 1-5 |
| max_service_temp | benefit | range midpoint |
| cost | cost | range midpoint, USD/kg |
| embodied_energy | cost | range midpoint, MJ/kg |
| recyclability | benefit | score 1-5 |

Cost and embodied energy are used on a linear scale (no logarithm). Consequence: materials that are all cheap look alike on cost and only expensive ones are penalised.

## 4. Weighting

Each part has default weights summing to 1. A **mission profile** multiplies each weight by a factor (table in `data/presets.json`, section `profiles`) and the result is renormalised:

`w_j = (base_j * modifier_j) / sum_k (base_k * modifier_k)`

| Profile | Main change |
|---|---|
| balanced | all modifiers 1 |
| endurance | performance x2.0, cost x0.6, recyclability x0.6, embodied x0.7, impact x0.8 |
| impact-tolerant | impact x2.5, performance x0.9, embodied and recyclability x0.8 |
| budget | cost x2.5, temperature x0.8, others x0.8-1.0 |
| eco | embodied energy x2.2, recyclability x2.2, performance and impact x0.9, cost and temperature x0.8 |

If the user supplies weights (UI sliders), they replace the resolved weights for the keys supplied; all weights are auto-normalised and rankings depend only on their proportions (tested).

## 5. TOPSIS (vector normalisation)

For decision matrix x (alternatives i, criteria j) and normalised weights w:

1. r_ij = x_ij / sqrt(sum_i x_ij^2)
2. v_ij = w_j * r_ij
3. Ideal A+ takes max v_ij for benefit criteria and min for cost criteria; anti-ideal A- the opposite.
4. D+_i = sqrt(sum_j (v_ij - A+_j)^2), D-_i = sqrt(sum_j (v_ij - A-_j)^2)
5. C_i = D-_i / (D+_i + D-_i), in [0, 1]. Higher is better. If D+ + D- = 0 the score is 0.5.

## 6. Weighted sum (min-max normalisation)

Benefit: n_ij = (x_ij - min_j) / (max_j - min_j). Cost: n_ij = (max_j - x_ij) / (max_j - min_j). A column with max = min is set to 0.5. Score S_i = sum_j w_j * n_ij in [0, 1].

## 7. Method agreement

Both methods are always computed. The app reports whether their top-3 **sets** are equal, whether their top-1 picks are equal, the size of the top-3 overlap and the Spearman rank correlation 1 - 6 sum(d^2) / (n (n^2 - 1)) between the two full rankings. Disagreement is information: it shows how method-dependent the answer is.

## 8. Monte Carlo robustness

Defaults: 2000 trials, seed 42, Dirichlet concentration 20, full property ranges. All values are configurable through the API (`trials` 100-20000, `seed`, `concentration` > 0 or `null` for fixed weights, `range_scale` 0-1).

Per trial:

1. Weights: w ~ Dirichlet(c * w0) where w0 are the user's normalised weights and c is the concentration. Larger c keeps weights closer to w0. For w0 = 0.35 and c = 20 the standard deviation of that weight is about 0.10.
2. Properties: density, modulus, strength, temperature, cost and embodied energy of every material are drawn independently and uniformly in [min, max] (scaled about the midpoint by `range_scale`; 0 collapses every range to its midpoint). The Ashby index is recomputed from the drawn property and density.
3. Impact and recyclability scores are fixed (ordinal scores have no defensible numeric uncertainty model).
4. All materials are scored with the selected method and ranked.

Everything is vectorised across trials (arrays of shape trials x materials x criteria); 2000 trials x 60 materials runs in a small fraction of a second (measured in `docs/VALIDATION.md`).

Outputs per material: P(rank 1), P(top 3), median rank, 5th and 95th percentile rank, full rank distribution, and a confidence label.

### Confidence label

`stability` = share of trials in which the material's rank is within **2 places of its baseline rank** (the non-random midpoint ranking).

| Label | Rule |
|---|---|
| High | stability >= 0.75 |
| Medium | 0.40 <= stability < 0.75 |
| Low | stability < 0.40 |

The label says how **stable a material's position** is under the stated uncertainty model. It is not a statement that the underlying data are correct. These constants are `STABILITY_BAND`, `HIGH_THRESHOLD`, `MEDIUM_THRESHOLD` in `robustness.py`.

## 9. Explainer

`contributions = w_j * n_ij` using the min-max normalisation of section 6, so a material's contributions add up to its weighted-sum score. The same bars are shown for TOPSIS, which is not additive; the interface says so. The sentence names up to two criteria where `w_j * (n_ij - mean_i n_ij)` is largest ("ranks first mainly because of...") and the single most negative one ("it loses points on...").

## 10. Compare

Up to three materials. Each criterion is min-max normalised over the **whole database**, with cost and embodied energy inverted so outward is always better. Raw midpoints are tabulated beside the radar chart.

## 11. Pareto front

For two chosen criteria (default cost vs performance index), a candidate is dominated if another candidate is at least as good on both (respecting direction) and strictly better on one. The front is the set of non-dominated candidates.

## 12. Requirement parser

`parser.py` is a fixed-vocabulary, rule-based reader (regular expressions; no machine learning, no network). It recognises part words, mission words, process words and numbers beside units (for example "under $40/kg", "70 C", "1500 kg/m3", "80 MPa"). Each rule that fires is returned with the words that triggered it.

## 13. Data basis (fairness of comparison)

- Fibre composites: laminate at roughly 50% fibre volume, in-plane properties of quasi-isotropic or balanced woven layups, not unidirectional.
- Printed polymers and composites: XY (in-plane) orientation, typical FDM settings.
- Foams: compressive modulus is used as the stiffness value.
- Honeycomb, PET foam and aerogel panels: effective values that only apply as a sandwich core; flagged in the results.
- Wood-type materials: values along the grain.
- All values are typical figures given as ranges and flagged `typical-value-needs-verification`. See `docs/DATA_VERIFICATION.md`.

## 14. Assumptions and limitations

See `ASSUMPTIONS.md` (decisions taken) and `KNOWN_LIMITATIONS.md` (what the tool does not do).
