# Assumptions

Each line: decision — reason.

- Python 3.11+ is required, but the build was developed on 3.13 — the pinned minimum in pyproject is 3.11 as requested.
- Dependencies are installed into the active interpreter via `pip install -e backend[dev]` — keeps `make setup` simple; a virtualenv is recommended but not forced.
- Material properties are typical handbook-style figures from general engineering knowledge, stored as min-max ranges and all flagged `typical-value-needs-verification` — no external database may be fetched or cited.
- Hard constraints are tested against property midpoints, and the feasible set is held fixed during Monte Carlo — keeps the candidate list explainable; sampling then only varies ranks within it.
- Ashby indices use E in GPa, strength in MPa and density in Mg/m3 — Ashby's convention; ranking is unit-independent.
- Foams, cork, honeycomb and aerogel panels use compressive modulus / effective strength as the stiffness and strength figures — these are the only meaningful numbers for them; flagged in `property_basis`.
- Cost and embodied energy are compared on a linear scale (no log transform) — simpler to explain; the consequence (cheap materials look alike) is listed in KNOWN_LIMITATIONS.
- Impact resistance and recyclability are integer 1-5 expert scores and are treated as exact in Monte Carlo — no defensible uncertainty model for ordinal scores.
- If the user supplies explicit weights they replace the part-and-profile weights (profile modifiers are not applied twice); partial weight dicts override only the keys given.
- Explainer contributions are the weighted-sum decomposition (weight x min-max value) for both methods — TOPSIS closeness is not additive; the bars therefore explain, but are not identical to, the TOPSIS score.
- Confidence label = share of Monte Carlo trials in which a material lands within +/-2 places of its baseline rank; High >= 0.75, Medium >= 0.40, otherwise Low — a single uniform rule that reads as "how stable is this position".
- Default Dirichlet concentration is 20 and default trials 2000 with seed 42 — gives weight noise of roughly +/-0.1 on a 0.35 weight; configurable per request.
- Two thermoplastic grades flagged with `caveat` (natural materials, aerogel, cork) — moisture, grain and batch variation are not modelled numerically.
- Quadcopter arm / plate / skin etc. use the Ashby index of their dominant load case (beam or panel, stiffness or strength); propeller and landing gear both use beam strength — the simplest defensible choice for a bending-limited blade or leg.
