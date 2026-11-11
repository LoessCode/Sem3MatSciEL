# Presenter guide

For someone presenting AirframeSelect without a materials-science background. Read the glossary first (10 minutes), then rehearse the demo once.

## The one-sentence pitch

"Choosing a material for a drone part is a trade-off between weight, strength, heat, crash toughness, cost and environmental impact. This tool ranks 47 materials for a chosen part, and, unlike a plain ranking, tells you **how confident** it is by re-running the ranking 2000 times with slightly different priorities and data."

## Before you start

```bash
make setup     # once
make demo      # then open http://localhost:8000
```

Tick **Presenter mode** (top right). Every panel then shows a one-line caption you can read aloud. Numbers below are what the shipped data produce; small changes appear if the data are edited.

## 5-minute demo script

**0:00 - What is on screen (30 s).** The page opens on "Quadcopter arm / Balanced". Say: "A drone arm is like a diving board: it must not bend when the motor pushes, and it must be light. We asked the tool for the best material."

**0:30 - The answer and its confidence (60 s).** Point to the headline: top pick bamboo laminate with a green **High** badge, and the sentence below it. Say: "It tells us *why*: very stiff for its weight and recyclable; it loses points on temperature. The badge says that when we shake the priorities and the data 2000 times, bamboo came first about 70% of the time and in the top three about 99% of the time." Point to the lower rows: "Aramid/epoxy is only Medium: its position is less certain."

**1:30 - Why, not just what (45 s).** Scroll to "Why these materials?". Say: "Each coloured segment is one factor. Blue is weight efficiency, orange crash toughness, yellow heat, green low cost. You can see what earned the score." Click another material in the table to change the bars' highlight and sentence.

**2:15 - Two methods (30 s).** Point to the TOPSIS / Weighted sum switch and the agreement indicator. Say: "There are two standard ways to combine factors. If they agree on the top three, the answer does not depend on the method. Here they differ slightly, and the tool tells us rather than hiding it."

**2:45 - A different job (60 s).** Click the demo **5-inch FPV quad arm**. Say: "FPV pilots crash a lot, so crash toughness is weighted heavily." Aramid/epoxy (Kevlar-type) becomes first with Medium confidence. Say: "That fits what builders know about aramid, and the lower confidence says it is a closer call." Then click **Eco-friendly 3D-printed battery enclosure**: "Now only printable materials qualify and sustainability matters, so polypropylene and recycled plastics lead."

**3:45 - The map (45 s).** Open **Ashby chart**. Say: "Every dot is a material. Higher means stiffer, further left means lighter. The dashed line connects materials that are equally good for this job. Above the line is better." Hover a dot to show its range bars.

**4:30 - Honesty (30 s).** Show the yellow data note. Say: "Values are typical figures, flagged as needing verification. The tool is for shortlisting, not for certification." Press **Download PDF report** to show the export.

## Ten likely examiner questions

1. **Where do the numbers come from?** Typical values from general engineering knowledge, stored as min-max ranges and flagged "needs verification" in the data and in every export. We checked them for plausibility (family bounds in `scripts/validate_data.py`) and `docs/DATA_VERIFICATION.md` is the checklist for verifying them against datasheets.
2. **What is an Ashby index?** One number that says how good a material is at a particular job per unit weight. For a beam that must not bend it is E^(1/2)/density. It comes from combining the stiffness requirement with the beam's mass.
3. **Why different indices for different parts?** The load case differs: a beam, a panel and a tie fail in different ways, so the exponents differ. Each part's rationale is shown in step 1 of the selector.
4. **What is TOPSIS and why two methods?** TOPSIS scores each material by closeness to an ideal best and distance from an ideal worst; the weighted sum scales each factor to 0-1 and adds. Two methods act as a cross-check; we report whether the top three agree and a rank correlation.
5. **How do you choose the weights?** Each part has defaults based on its load case; the mission profile multiplies them by documented factors; the user can move sliders. Because weights are subjective, the robustness analysis varies them.
6. **How does the Monte Carlo work and what does High confidence mean?** 2000 seeded trials draw weights from a Dirichlet distribution centred on the user's weights and each property uniformly inside its range, then re-rank. High means the material stays within two places of its baseline rank in at least 75% of trials (Medium 40-75%, Low below 40%). It describes stability, not data correctness.
7. **Why does bamboo or plywood rank so high for a drone arm?** Wood-type materials really are very stiff for their weight (an Ashby chart staple) and score well on cost, embodied energy and recyclability. The tool does not model moisture, grain variation or joints, which is why those materials carry a caveat flag. A different mission (impact-tolerant) puts aramid first.
8. **Is this new?** To our knowledge it is a free, open-source, UAV-specific combination of part-specific Ashby indices, two transparent ranking methods, Monte Carlo confidence, explanations and printing/sustainability lenses. We do not claim nothing similar exists (`docs/NOVELTY_AND_UTILITY.md`).
9. **How did you test it?** 90+ automated tests including a TOPSIS calculation done independently by hand-arithmetic code, physical sanity checks (carbon/epoxy beats aluminium 6061 and PLA on beam stiffness even worst-case vs best-case), seeded reproducibility, probability sums, and API tests. `docs/VALIDATION.md` lists the results.
10. **What are the limits?** Typical data, simple beam/panel models, judgement scores for impact and recyclability, a uniform-range uncertainty model, and no moisture, fatigue or joint modelling (`KNOWN_LIMITATIONS.md`). It shortlists; it does not certify.

## Plain-language glossary

- **Density**: how heavy a material is for its size.
- **Stiffness (Young's modulus)**: how much it resists bending or stretching.
- **Strength**: how hard you can pull before it breaks.
- **Toughness / impact resistance**: how well it survives a crash without cracking.
- **Service temperature**: the hottest it can safely run before it softens or weakens.
- **Embodied energy**: energy used to make a kilogram of it, a rough footprint measure.
- **Composite**: fibres (carbon, glass, aramid) held in a plastic (epoxy), giving high strength for low weight.
- **Quasi-isotropic laminate**: a layup with fibres in several directions so it is similarly stiff every way in the plane.
- **Ashby index**: a "how good per kilogram for this job" number.
- **TOPSIS / weighted sum**: two ways of combining factors into one score.
- **Monte Carlo**: repeating a calculation many times with random variation to see how much the answer moves.
- **Pareto front**: the options that are not beaten on both of two factors at once.
