# Novelty and utility

## Statement of novelty (worded conservatively)

To our knowledge, AirframeSelect is a free, open-source, UAV-component-specific material-selection tool that combines, in one offline application:

1. **Ashby performance indices tied to each part's load case** (arm = beam stiffness, fuselage skin = panel stiffness, and so on), with the index range propagated from property ranges;
2. **transparent multi-criteria ranking** with both TOPSIS and a weighted sum, and an explicit report of whether they agree;
3. **uncertainty-aware ranking** by Monte Carlo analysis that perturbs both the user's weights and the material data, reporting P(rank 1), P(top 3), median rank and a High / Medium / Low confidence label;
4. **explainable per-criterion contributions** with a generated plain-English sentence for every material;
5. **manufacturability and sustainability lenses** suited to 3D-printed and hobby-scale builds (required process, printable composites, recycled filaments, embodied energy, recyclability).

We have not surveyed every tool in existence and make no claim that nothing similar exists. The claim is about the combination in a free, UAV-focused package that can be inspected end to end.

## Contrast with generic TOPSIS scripts

A typical generic TOPSIS script takes a user-supplied matrix and weights and returns one ranking. AirframeSelect adds, around the same well-known method: a curated UAV material set with ranges instead of single numbers; part-specific Ashby indices so the "performance" column is derived from a load case rather than typed in; hard constraints with reasons for each exclusion; a second method as a cross-check; a robustness analysis that says how much the ranking can be trusted; and explanations, charts and exports for non-experts.

## Contrast with commercial selection software

Commercial materials-selection packages are mature, broad and built around large validated databases; this project does not compete with that and is not a substitute for it. What a project like this can offer, without us asserting feature gaps in any specific product, is: free and open code that can be read and modified end to end, a dataset deliberately focused on UAV parts, hobby filaments and recycled options, a method that is explained in the interface, and an uncertainty analysis whose design (Dirichlet weights, uniform data ranges, documented thresholds) is fully visible. Its data are typical figures that must be verified; a commercial database would be the right place to get validated properties.

## Utility

- **Students and hobbyists** get a defensible first-pass shortlist for an arm, plate, propeller, landing gear, battery box or skin, with the reasoning shown.
- **Teaching:** the app makes the trade-offs visible (Ashby chart, Pareto front, radar comparison) and shows why a ranking is or is not stable.
- **Decision hygiene:** the confidence label stops a narrow numerical win from being mistaken for a clear one.
- **Reproducibility:** everything runs offline, results are seeded and exportable (CSV and PDF with assumptions and the data-verification disclaimer).

## What it is not

It is not a certification or structural-analysis tool. It does not model buckling details, joints, fatigue, moisture, manufacturing defects or cost of tooling. Use it to shortlist, then verify with datasheets and testing.
