# College report outline, mapped to repository artifacts

| # | Section | Content to write | Where to find the material |
|---|---|---|---|
| 1 | Title page and abstract | Problem, method, headline result, one-sentence confidence finding | `README.md`, `docs/NOVELTY_AND_UTILITY.md` |
| 2 | Introduction | Why material choice matters for drones (mass, endurance, crash tolerance, cost, sustainability) | `docs/PRESENTER_GUIDE.md` (plain-language framing) |
| 3 | Objectives and scope | Parts covered, what is out of scope | `data/presets.json` (parts), `KNOWN_LIMITATIONS.md` |
| 4 | Materials-science background | Density, modulus, strength, toughness, glass-transition / service temperature, composites, anisotropy, embodied energy | `docs/PRESENTER_GUIDE.md` glossary, app Methodology page |
| 5 | Ashby method | Performance indices derived from load cases, log-log charts, guide lines | `docs/METHODOLOGY.md` sections 1 and 11, `backend/src/airframeselect/ashby.py`, Ashby tab |
| 6 | Data | Families, ranges, property basis, verification status | `data/materials.json`, `docs/DATA_VERIFICATION.md`, `scripts/validate_data.py` |
| 7 | Decision method | Constraints, TOPSIS, weighted sum, weights and mission profiles | `docs/METHODOLOGY.md` sections 2 to 7, `mcdm.py`, `constraints.py` |
| 8 | Uncertainty and robustness | Monte Carlo design, confidence labels | `docs/METHODOLOGY.md` section 8, `robustness.py` |
| 9 | Software design | Architecture, API, front end | `README.md`, `CLAUDE.md`, `/api/docs` when the server runs |
| 10 | Verification and validation | Test list, hand-calculated TOPSIS, physical sanity checks, seed stability | `backend/tests/`, `docs/VALIDATION.md`, `scripts/make_validation_report.py` |
| 11 | Case studies | The three demo scenarios, discussion of top picks and confidence | App demo buttons, `docs/VALIDATION.md` section 3, exported PDFs |
| 12 | Discussion | Which results surprised you and why (for example natural materials scoring well); sensitivity to weights; method disagreement | `docs/VALIDATION.md` section 2 and 4, `KNOWN_LIMITATIONS.md` |
| 13 | Limitations and future work | Data verification, moisture/fatigue, orthotropy, finer uncertainty models | `KNOWN_LIMITATIONS.md`, `ASSUMPTIONS.md` |
| 14 | Conclusion | What was learnt, how the tool should be used | |
| 15 | References | List only the textbooks, datasheets and handbooks you actually consulted while verifying the data | `docs/DATA_VERIFICATION.md` (record the source per row) |
| App. A | Source listing / repository link | | repository root |
| App. B | Data verification table with ticked boxes and sources | | `docs/DATA_VERIFICATION.md` |
| App. C | Sample exported PDF and CSV | | Export buttons in the app |
