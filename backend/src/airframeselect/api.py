"""FastAPI layer: thin, validated HTTP wrapper over the pure-Python engine."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .data import data_dir, load_materials_doc, load_presets
from .exporting import build_csv, build_pdf
from .pipeline import (
    InputError, run_ashby, run_compare, run_pareto, run_ranking, run_robustness,
)
from .parser import parse_requirement

Weight = Annotated[float, Field(ge=0, le=1e6, allow_inf_nan=False)]

app = FastAPI(
    title="AirframeSelect API",
    version=__version__,
    description="Material selection decision framework for UAV airframe parts: Ashby indices, "
    "TOPSIS / weighted-sum ranking and Monte Carlo robustness analysis. Material values are typical "
    "figures that need verification against datasheets.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConstraintsIn(BaseModel):
    """Only fields that are sent override the part defaults; send null to remove a limit."""

    model_config = ConfigDict(extra="forbid")
    max_density_kg_m3: float | None = Field(None, gt=0, le=1e5, allow_inf_nan=False)
    min_strength_MPa: float | None = Field(None, gt=0, le=1e5, allow_inf_nan=False)
    min_service_temp_C: float | None = Field(None, gt=0, le=5000, allow_inf_nan=False)
    max_cost_usd_per_kg: float | None = Field(None, gt=0, le=1e6, allow_inf_nan=False)
    required_process: Literal["fdm", "layup", "machining", "injection", "sheet-forming", "cnc-cut"] | None = None


class RankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    part: str = Field(..., examples=["arm"])
    profile: str = Field("balanced", examples=["balanced"])
    weights: dict[str, Weight] | None = Field(None, description="Optional criteria weights; replace the profile weights.")
    constraints: ConstraintsIn | None = None
    method: Literal["topsis", "wsm"] = "topsis"

    def engine_kwargs(self) -> dict[str, Any]:
        return {
            "part_id": self.part,
            "profile_id": self.profile,
            "weights": self.weights,
            "constraints": self.constraints.model_dump(exclude_unset=True) if self.constraints else None,
            "method": self.method,
        }


class RobustnessRequest(RankRequest):
    trials: int = Field(2000, ge=100, le=20000)
    seed: int = Field(42, ge=0, le=2**31 - 1)
    concentration: float | None = Field(20.0, gt=0, le=10000, allow_inf_nan=False, description="Dirichlet concentration; null = fixed weights.")
    range_scale: float = Field(1.0, ge=0, le=1, description="1 = full property ranges, 0 = midpoints only.")

    def mc_kwargs(self) -> dict[str, Any]:
        return {**self.engine_kwargs(), "trials": self.trials, "seed": self.seed,
                "concentration": self.concentration, "range_scale": self.range_scale}


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_ids: list[str] = Field(..., min_length=1, max_length=3)
    part: str = "arm"


class AshbyRequest(RankRequest):
    axes: Literal["density_vs_strength", "density_vs_modulus", "cost_vs_strength"] = "density_vs_modulus"
    top_n: int = Field(5, ge=0, le=50)


class ParetoRequest(RankRequest):
    x_criterion: Literal["performance_index", "impact_resistance", "max_service_temp", "cost", "embodied_energy", "recyclability"] = "cost"
    y_criterion: Literal["performance_index", "impact_resistance", "max_service_temp", "cost", "embodied_energy", "recyclability"] = "performance_index"


class ParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., max_length=1000)


@app.exception_handler(InputError)
async def input_error_handler(_: Request, exc: InputError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {"status": "ok", "version": __version__, "materials": len(load_materials_doc()["materials"])}


@app.get("/api/materials", tags=["data"])
def materials() -> dict[str, Any]:
    return load_materials_doc()


@app.get("/api/presets", tags=["data"])
def presets() -> dict[str, Any]:
    return load_presets()


@app.post("/api/rank", tags=["analysis"])
def rank(req: RankRequest) -> dict[str, Any]:
    return run_ranking(**req.engine_kwargs())


@app.post("/api/robustness", tags=["analysis"])
def robustness(req: RobustnessRequest) -> dict[str, Any]:
    return run_robustness(**req.mc_kwargs())


@app.post("/api/compare", tags=["analysis"])
def compare(req: CompareRequest) -> dict[str, Any]:
    return run_compare(req.material_ids, req.part)


@app.post("/api/ashby", tags=["analysis"])
def ashby(req: AshbyRequest) -> dict[str, Any]:
    return run_ashby(**req.engine_kwargs(), axes=req.axes, top_n=req.top_n)


@app.post("/api/pareto", tags=["analysis"])
def pareto(req: ParetoRequest) -> dict[str, Any]:
    return run_pareto(**req.engine_kwargs(), x_criterion=req.x_criterion, y_criterion=req.y_criterion)


@app.post("/api/parse", tags=["analysis"])
def parse(req: ParseRequest) -> dict[str, Any]:
    """Rule-based (non-LLM) reading of a plain-English requirement into form fields."""
    return parse_requirement(req.text)


@app.post("/api/export/csv", tags=["export"])
def export_csv(req: RobustnessRequest) -> Response:
    ranking = run_ranking(**req.engine_kwargs())
    rob = run_robustness(**req.mc_kwargs())
    return Response(
        content=build_csv(ranking, rob),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="airframeselect_{req.part}_{req.profile}.csv"'},
    )


@app.post("/api/export/pdf", tags=["export"])
def export_pdf(req: RobustnessRequest) -> Response:
    ranking = run_ranking(**req.engine_kwargs())
    rob = run_robustness(**req.mc_kwargs())
    return Response(
        content=build_pdf(ranking, rob),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="airframeselect_{req.part}_{req.profile}.pdf"'},
    )


def _static_dir() -> Path | None:
    env = os.environ.get("AIRFRAMESELECT_STATIC_DIR")
    candidates = [Path(env)] if env else [data_dir().parent / "frontend" / "dist"]
    for c in candidates:
        if (c / "index.html").is_file():
            return c
    return None


_static = _static_dir()
if _static is not None:
    # Registered last so /api/* routes take priority; serves the built single-page app.
    app.mount("/", StaticFiles(directory=_static, html=True), name="frontend")
