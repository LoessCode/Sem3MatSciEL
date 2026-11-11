# Assumptions

Each line: decision — reason.

- Python 3.11+ is required, but the build was developed on 3.13 — the pinned minimum in pyproject is 3.11 as requested.
- Dependencies are installed into the active interpreter via `pip install -e backend[dev]` — keeps `make setup` simple; a virtualenv is recommended but not forced.
