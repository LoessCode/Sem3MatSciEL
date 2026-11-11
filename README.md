# AirframeSelect

**A decision framework for material selection in drone airframes, with a confidence level.**

AirframeSelect recommends materials for UAV structural parts (quadcopter arm, frame plate, propeller, landing gear, battery enclosure, fuselage skin). It ranks 47 materials with transparent multi-criteria methods and shows **how confident** each recommendation is by re-running the ranking 2000 times with perturbed priorities and data. It runs fully offline: no API keys, no paid services, no LLM calls.

To our knowledge it is a free, open-source, UAV-component-specific tool that combines (a) Ashby performance indices tied to each part's load case, (b) TOPSIS and weighted-sum ranking, (c) Monte Carlo robustness analysis, (d) explainable per-criterion contributions and (e) manufacturability and sustainability lenses for 3D-printed and hobby-scale builds. See [docs/NOVELTY_AND_UTILITY.md](docs/NOVELTY_AND_UTILITY.md).

> **Data note:** all material values are typical figures stored as min-max ranges and flagged `typical-value-needs-verification`. Spot-check them against supplier datasheets before relying on any result ([docs/DATA_VERIFICATION.md](docs/DATA_VERIFICATION.md)).

## Features

- Stepper: part, mission profile, hard limits, weight sliders with plain-language tooltips; three one-click demo scenarios; a keyword-based "describe it in words" form filler.
- Ranking table with score, chance of rank 1, High/Medium/Low confidence badge and flags; TOPSIS / weighted-sum toggle with an agreement indicator.
- Explainer: stacked per-criterion contribution bars and a generated plain-English sentence.
- Robustness charts: chance of #1 and top 3, and a rank distribution per material.
- Excluded-materials list with a reason for each.
- Ashby chart (log-log, range bars, guide line for the selected index), Pareto-front view, 3-material compare (radar plus table), Methodology page with glossary.
- Presenter mode: a one-line caption on every panel.
- CSV and PDF export (inputs, ranking, robustness summary, explanation, assumptions, data disclaimer).
- CLI: `python -m airframeselect rank --part arm --profile balanced`.

## Quick start

Requirements: Python 3.11+, Node 20+ with npm.

```bash
make setup     # install backend (editable) and frontend dependencies
make test      # backend tests + frontend typecheck
make demo      # build the UI, then serve UI and API together on http://localhost:8000
make smoke     # start a server, call every endpoint, exit 0 on success
```

Development with hot reload (backend on :8000, Vite on :5173 with an `/api` proxy):

```bash
make dev
```

Docker (multi-stage: builds the frontend, serves it from FastAPI):

```bash
docker build -t airframeselect .
docker run --rm -p 8000:8000 airframeselect
```

Interactive API docs are at `http://localhost:8000/api/docs`.

### CLI example

```bash
python -m airframeselect rank --part arm --profile balanced --robustness --top 5
```

## Architecture

```
backend/src/airframeselect/    pure-Python engine (numpy only) + thin FastAPI layer
  data.py          dataset loading and array views
  ashby.py         performance indices, range propagation, guide lines
  constraints.py   hard-constraint filter with plain-language reasons
  mcdm.py          TOPSIS, weighted sum, rank correlation, method agreement
  robustness.py    vectorised Monte Carlo (Dirichlet weights, uniform data ranges)
  explain.py       contributions and generated sentences
  compare.py       radar-chart data
  pareto.py        Pareto-front analysis
  parser.py        rule-based requirement parser
  pipeline.py      orchestration used by API, CLI and exports
  exporting.py     CSV and PDF (reportlab)
  api.py           FastAPI endpoints (Pydantic v2)
  cli.py           command-line interface
backend/tests/     pytest suite (engine, API, data validation, docs)
frontend/          React + TypeScript + Vite + Tailwind + Recharts
data/              materials.json, presets.json
scripts/           validate_data.py, make_validation_report.py, make_data_verification.py, smoke.py
docs/              METHODOLOGY, NOVELTY_AND_UTILITY, PRESENTER_GUIDE, DATA_VERIFICATION, REPORT_OUTLINE, VALIDATION
```

### API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness and dataset size |
| GET | `/api/materials` | the full material database |
| GET | `/api/presets` | criteria, indices, parts, profiles, demo scenarios |
| POST | `/api/rank` | constraint filter, TOPSIS and weighted-sum ranking, explanations |
| POST | `/api/robustness` | Monte Carlo statistics and confidence labels |
| POST | `/api/compare` | up to 3 materials, normalised values for a radar chart |
| POST | `/api/ashby` | scatter data with ranges, selectable axes, guide line |
| POST | `/api/pareto` | Pareto front over two criteria |
| POST | `/api/parse` | keyword-based requirement parser |
| POST | `/api/export/csv`, `/api/export/pdf` | downloadable ranking |

Invalid input returns HTTP 422 with a `detail` message.

## Method in brief

1. The part's load case fixes an Ashby index (for example beam stiffness E^(1/2)/rho for an arm).
2. Hard limits remove unsuitable materials, each with a reason.
3. Six criteria (performance index, impact resistance, service temperature, cost, embodied energy, recyclability) are weighted using part defaults times a mission profile (or your sliders).
4. TOPSIS and a min-max weighted sum rank the survivors; agreement is reported.
5. Monte Carlo (default 2000 seeded trials) perturbs weights (Dirichlet) and properties (uniform within ranges). Confidence label: share of trials within 2 places of the baseline rank, High at 75% or more, Medium at 40% or more, otherwise Low.

Full detail: [docs/METHODOLOGY.md](docs/METHODOLOGY.md). Verification results: [docs/VALIDATION.md](docs/VALIDATION.md). Presenting: [docs/PRESENTER_GUIDE.md](docs/PRESENTER_GUIDE.md). Report mapping: [docs/REPORT_OUTLINE.md](docs/REPORT_OUTLINE.md). Decisions and limits: [ASSUMPTIONS.md](ASSUMPTIONS.md), [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).

## Regenerating generated files

```bash
python scripts/make_validation_report.py     # docs/VALIDATION.md
python scripts/make_data_verification.py     # docs/DATA_VERIFICATION.md
python scripts/validate_data.py              # data checks (also run inside pytest)
```
