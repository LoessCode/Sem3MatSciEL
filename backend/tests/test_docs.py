import json
import re
from pathlib import Path

from airframeselect import robustness

ROOT = Path(__file__).resolve().parents[2]
DOCS = ["METHODOLOGY.md", "NOVELTY_AND_UTILITY.md", "PRESENTER_GUIDE.md", "DATA_VERIFICATION.md", "REPORT_OUTLINE.md", "VALIDATION.md"]


def test_required_docs_exist_and_nonempty():
    for name in DOCS:
        assert (ROOT / "docs" / name).stat().st_size > 500, name
    for name in ["README.md", "CLAUDE.md", "ASSUMPTIONS.md", "KNOWN_LIMITATIONS.md", "Makefile", "Dockerfile"]:
        assert (ROOT / name).is_file(), name


def test_data_verification_lists_every_material_with_checkboxes():
    text = (ROOT / "docs" / "DATA_VERIFICATION.md").read_text()
    mats = json.loads((ROOT / "data" / "materials.json").read_text())["materials"]
    for m in mats:
        assert f"`{m['id']}`" in text, m["id"]
    assert text.count("[ ]") >= len(mats) * 8
    assert "needs-verification" in text


def test_methodology_matches_code_constants():
    text = (ROOT / "docs" / "METHODOLOGY.md").read_text()
    assert f"stability >= {robustness.HIGH_THRESHOLD}" in text
    assert f"0.40 <= stability < {robustness.HIGH_THRESHOLD}" in text
    assert f"within **{robustness.STABILITY_BAND} places" in text
    for formula in ["E^(1/2) / rho", "sigma^(2/3) / rho", "E^(1/3) / rho", "sigma^(1/2) / rho", "E / rho", "sigma / rho"]:
        assert formula in text


def test_readme_documents_every_endpoint():
    readme = (ROOT / "README.md").read_text()
    from airframeselect.api import app
    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/") and "docs" not in path and "redoc" not in path and "openapi" not in path:
            assert path in readme, path


def test_no_todo_or_placeholder_text_in_repo():
    bad = re.compile(r"\b(TODO|FIXME|TBD|lorem ipsum|XXX)\b", re.I)
    skip = {"node_modules", "dist", ".git", "__pycache__", ".pytest_cache", "package-lock.json"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or set(p.relative_to(ROOT).parts) & skip or p.suffix in {".png", ".pdf", ".svg", ".pyc"}:
            continue
        if p.name == "test_docs.py":
            continue
        if "egg-info" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert not bad.search(text), f"placeholder text in {p.relative_to(ROOT)}"


def test_novelty_wording_is_hedged():
    text = (ROOT / "docs" / "NOVELTY_AND_UTILITY.md").read_text()
    assert "To our knowledge" in text
    assert not re.search(r"\b(the first|unique|no other tool)\b", text.lower())
