PY ?= python3

.PHONY: setup dev test build demo smoke validate

setup:
	$(PY) -m pip install -e "backend[dev]"
	cd frontend && npm install

dev:
	@echo "Backend on http://localhost:8000 (API docs at /api/docs), frontend on http://localhost:5173"
	@bash -c 'trap "kill 0" EXIT; $(PY) -m uvicorn airframeselect.api:app --port 8000 --reload --reload-dir backend/src & (cd frontend && npm run dev) & wait'

test:
	cd backend && $(PY) -m pytest -q
	cd frontend && npm run typecheck

build:
	cd frontend && npm run build

demo: build
	$(PY) -m uvicorn airframeselect.api:app --host 0.0.0.0 --port 8000

smoke:
	$(PY) scripts/smoke.py

validate:
	$(PY) scripts/validate_data.py
