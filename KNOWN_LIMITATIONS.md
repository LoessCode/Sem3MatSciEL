# Known limitations

1. **Data are typical values, not verified.** Every record is flagged `typical-value-needs-verification`. Spot-check against datasheets before relying on a result (`docs/DATA_VERIFICATION.md`).
2. **Simple physics.** Ashby indices assume idealised beam, panel or tie behaviour. Buckling details, joints and fasteners, fatigue, creep, vibration, moisture uptake and manufacturing defects are not modelled.
3. **Natural materials score strongly.** Bamboo laminate and plywood often rank first because they are very stiff for their weight, cheap and have low embodied energy. Moisture, grain direction, adhesive quality and batch variation are not modelled; they are flagged with a caveat rather than penalised numerically. Their service temperature is set low (60-80 C) because adhesives and moisture limit it.
4. **Orthotropy is reduced to one number.** Composites and wood use in-plane or along-grain values; unidirectional laminates are not included and directional design is out of scope.
5. **Linear cost and energy scales.** Cost and embodied energy are not log-transformed, so many cheap materials look alike on cost.
6. **Judgement scores.** Impact resistance and recyclability are 1-5 scores, treated as exact in Monte Carlo.
7. **Uniform uncertainty model.** Property values are sampled uniformly inside their min-max range, a modelling choice and not a measured distribution. Properties are sampled independently (no correlation between, for example, density and modulus).
8. **Constraints on midpoints.** Hard limits use range midpoints and the feasible set is fixed during Monte Carlo, so a material near a limit is not tested for being feasible in some trials.
9. **Explainer is a weighted-sum decomposition.** TOPSIS closeness is not additive, so the contribution bars add up exactly only to the weighted-sum score.
10. **Core materials need a sandwich.** Honeycomb, PET foam and aerogel panels use effective core values and are only meaningful bonded between skins (flagged "Sandwich core only").
11. **Requirement parser is keyword-based.** It understands a fixed vocabulary and number-plus-unit patterns; it is not natural-language understanding and always shows which words it used.
12. **Single-user, local tool.** No authentication, persistence or multi-user features; the Monte Carlo seed is configurable but the UI uses 42.
13. **Browser support** was checked with a current Chromium only.
14. **Dockerfile not built in the authoring environment** (no Docker daemon was available). It repeats the steps that `make setup`, `make build` and `make demo` run and that were verified from a fresh clone; build it once with `docker build -t airframeselect .` to confirm.
