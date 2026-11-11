#!/usr/bin/env python3
"""Start the server in the background, call every endpoint, check responses, shut down.

Exit code 0 on success. Uses only the standard library for HTTP.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(base: str, method: str, path: str, body: dict | None = None) -> tuple[int, bytes, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def main() -> int:
    port = int(os.environ.get("SMOKE_PORT", free_port()))
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend" / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "airframeselect.api:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    try:
        for _ in range(100):
            try:
                if call(base, "GET", "/api/health")[0] == 200:
                    break
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.2)
        else:
            print("server did not start")
            return 1
        print(f"Smoke test against {base}")
        base_req = {"part": "arm", "profile": "balanced"}
        s, b, _ = call(base, "GET", "/api/health")
        check("GET /api/health", s == 200 and json.loads(b)["status"] == "ok")
        s, b, _ = call(base, "GET", "/api/materials")
        check("GET /api/materials", s == 200 and len(json.loads(b)["materials"]) >= 45)
        s, b, _ = call(base, "GET", "/api/presets")
        check("GET /api/presets", s == 200 and len(json.loads(b)["parts"]) == 6)
        s, b, _ = call(base, "POST", "/api/rank", base_req)
        j = json.loads(b)
        check("POST /api/rank", s == 200 and j["ranking"][0]["rank"] == 1 and len(j["excluded"]) > 0)
        s, b, _ = call(base, "POST", "/api/robustness", {**base_req, "trials": 500})
        j = json.loads(b)
        check("POST /api/robustness", s == 200 and abs(sum(j["materials"][0]["rank_distribution"]) - 1) < 1e-9)
        s, b, _ = call(base, "POST", "/api/compare", {"material_ids": ["cfrp-qi", "al6061", "pla"], "part": "arm"})
        check("POST /api/compare", s == 200 and len(json.loads(b)["materials"]) == 3)
        s, b, _ = call(base, "POST", "/api/ashby", {**base_req, "axes": "density_vs_modulus"})
        j = json.loads(b)
        check("POST /api/ashby", s == 200 and j["guide"] is not None and len(j["points"]) >= 45)
        s, b, h = call(base, "POST", "/api/pareto", {**base_req})
        check("POST /api/pareto", s == 200 and any(p["pareto"] for p in json.loads(b)["points"]))
        s, b, _ = call(base, "POST", "/api/parse", {"text": "a cheap 3D printed battery box that survives 70 C"})
        check("POST /api/parse", s == 200 and json.loads(b)["part"] == "battery_enclosure")
        s, b, h = call(base, "POST", "/api/export/csv", {**base_req, "trials": 200})
        check("POST /api/export/csv", s == 200 and b"rank" in b and h.get("content-type", "").startswith("text/csv"))
        s, b, h = call(base, "POST", "/api/export/pdf", {**base_req, "trials": 200})
        check("POST /api/export/pdf", s == 200 and b.startswith(b"%PDF"))
        s, _, _ = call(base, "POST", "/api/rank", {"part": "nonexistent"})
        check("422 on unknown part", s == 422)
        s, _, _ = call(base, "POST", "/api/robustness", {**base_req, "trials": 1})
        check("422 on invalid trials", s == 422)
        s, _, _ = call(base, "GET", "/api/docs")
        check("GET /api/docs", s == 200)
        if (ROOT / "frontend" / "dist" / "index.html").is_file():
            s, b, _ = call(base, "GET", "/")
            check("GET / serves built frontend", s == 200 and b"<div id=\"root\">" in b)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    if failures:
        print(f"SMOKE FAILED: {failures}")
        return 1
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
