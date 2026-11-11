# CLAUDE.md — AirframeSelect

## Project summary
AirframeSelect is an offline, open-source decision framework that recommends materials for UAV (drone)
structural parts and shows how confident each recommendation is. Academic project for a 1-credit
Materials Science experiential-learning course. Every user-facing screen must explain itself in plain language.

Novelty (always worded "to our knowledge"): a free, open-source, UAV-component-specific tool combining
(a) Ashby performance indices tied to each part's load case, (b) transparent MCDM ranking (TOPSIS + weighted sum),
(c) uncertainty-aware ranking by Monte Carlo robustness analysis, (d) explainable per-criterion contributions,
(e) manufacturability and sustainability lenses for 3D-printed / hobby-scale builds.

## Architecture
- `backend/src/airframeselect/` — pure-Python engine (numpy only; no web deps). Modules: data loading, ashby,
  constraints, mcdm, robustness, explain, compare, pipeline, exports (csv/pdf), cli.
- `backend/src/airframeselect/api.py` — thin FastAPI layer (Pydantic v2).
- `backend/tests/` — pytest.
- `frontend/` — React + TypeScript + Vite + Tailwind + Recharts. Vite dev proxy `/api` -> :8000.
- `data/materials.json`, `data/presets.json` — datasets (typical values, ALL flagged needs-verification).
- `scripts/` — validate_data.py, make_validation_report.py, smoke.py.
- `docs/` — METHODOLOGY, NOVELTY_AND_UTILITY, PRESENTER_GUIDE, DATA_VERIFICATION, REPORT_OUTLINE, VALIDATION.

## Commands
- `make setup` — install backend (pip, editable) and frontend (npm) deps
- `make dev` — backend :8000 + Vite dev server
- `make test` — pytest + frontend typecheck
- `make build` — build frontend into frontend/dist
- `make demo` — one process on :8000 serving built UI + API
- `make smoke` — scripts/smoke.py
- CLI: `python -m airframeselect rank --part arm --profile balanced`

## Conventions
- Never invent citations, URLs, DOIs, standards numbers or page numbers. Generic source types only.
- No network at runtime, no LLM calls, no API keys.
- No TODOs / placeholders in the final repo. Ambiguities -> ASSUMPTIONS.md; cut features -> KNOWN_LIMITATIONS.md.
- Novelty wording: "to our knowledge", never absolute.
- Commit after each phase; run backend tests + frontend typecheck/build before moving on.

## PROGRESS
- [x] Phase 0 scaffold + CLAUDE.md
- [x] Phase 1 data + validator
- [x] Phase 2 engine + tests
- [x] Phase 3 API + tests
- [ ] Phase 4 frontend selector + results
- [ ] Phase 5 Ashby chart, compare view, methodology page
- [ ] Phase 6 exports (CSV, PDF)
- [ ] Phase 7 docs + validation report
- [ ] Phase 8 polish, accessibility, Dockerfile, smoke script
- [ ] Phase 9 requirement parser + Pareto view
