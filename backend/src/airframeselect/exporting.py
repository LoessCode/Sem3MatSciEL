"""CSV and PDF exports of a ranking (reportlab only, no system dependencies)."""
from __future__ import annotations

import csv
import io
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import __version__
from .data import CRITERIA, load_materials_doc, load_presets

DISCLAIMER = (
    "Data-verification disclaimer: all material values in this tool are typical figures from general "
    "engineering knowledge, stored as ranges, and every record is flagged 'typical-value-needs-verification'. "
    "They must be spot-checked against supplier datasheets or an engineering handbook before this ranking is "
    "relied on for any design decision."
)

ASSUMPTIONS = [
    "Hard constraints are tested against property midpoints; the feasible set is then held fixed.",
    "Performance index = Ashby index for the part's dominant load case, computed from midpoints (range shown separately).",
    "TOPSIS uses vector normalisation; the weighted sum uses min-max normalisation. Weights are normalised to sum to 1.",
    "Monte Carlo draws weights from a Dirichlet distribution centred on the chosen weights and properties uniformly within their ranges; impact and recyclability scores are treated as exact.",
    "Confidence label = share of trials in which a material stays within 2 places of its baseline rank (High >= 75%, Medium >= 40%, otherwise Low).",
    "Fibre composites use quasi-isotropic or balanced woven laminate values; printed materials use XY (in-plane) values.",
]

CSV_COLUMNS = [
    "rank", "material", "family", "score", "topsis_score", "wsm_score",
    "perf_index_min", "perf_index_mid", "perf_index_max",
    "density_kg_m3", "youngs_modulus_GPa", "tensile_strength_MPa", "max_service_temp_C",
    "cost_usd_per_kg", "embodied_energy_MJ_per_kg", "impact_resistance", "recyclability",
    "p_rank1", "p_top3", "median_rank", "confidence", "flags", "explanation",
]


def build_csv(ranking: dict[str, Any], robustness: dict[str, Any]) -> bytes:
    rob = {m["id"]: m for m in robustness.get("materials", [])}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow([f"# AirframeSelect ranking: part={ranking['inputs']['part']['id']} profile={ranking['inputs']['profile']['id']} "
                f"method={ranking['inputs']['method']}. Values are typical figures needing verification."])
    w.writerow(CSV_COLUMNS)
    for r in ranking["ranking"]:
        v = r["values"]
        m = rob.get(r["id"], {})
        w.writerow([
            r["rank"], r["name"], r["family"], f"{r['score']:.4f}", f"{r['topsis_score']:.4f}", f"{r['wsm_score']:.4f}",
            f"{r['performance_index']['min']:.3f}", f"{r['performance_index']['mid']:.3f}", f"{r['performance_index']['max']:.3f}",
            f"{v['density_kg_m3']:g}", f"{v['youngs_modulus_GPa']:g}", f"{v['tensile_strength_MPa']:g}",
            f"{v['max_service_temp_C']:g}", f"{v['cost_usd_per_kg']:g}", f"{v['embodied_energy_MJ_per_kg']:g}",
            int(v["impact_resistance"]), int(v["recyclability"]),
            f"{m['p_rank1']:.3f}" if m else "", f"{m['p_top3']:.3f}" if m else "",
            f"{m['median_rank']:g}" if m else "", m.get("confidence", ""),
            "; ".join(r["flags"]), r["explanation"],
        ])
    return ("﻿" + buf.getvalue()).encode("utf-8")


def _bar_table(items: list[tuple[str, float]], width_mm: float = 70.0) -> Table:
    """A small horizontal bar chart: label, a coloured bar proportional to value (0..1), percentage."""
    rows = []
    for label, val in items:
        bar = Table([[""]], colWidths=[max(0.5, val * width_mm) * mm], rowHeights=[3.5 * mm])
        bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0072B2"))]))
        rows.append([label, bar, f"{val*100:.0f}%"])
    t = Table(rows, colWidths=[55 * mm, (width_mm + 2) * mm, 14 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t


def build_pdf(ranking: dict[str, Any], robustness: dict[str, Any]) -> bytes:
    inp = ranking["inputs"]
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9, leading=12)
    small = ParagraphStyle("small", parent=body, fontSize=7.5, leading=9.5)
    warn = ParagraphStyle("warn", parent=body, backColor=colors.HexColor("#FFF4D6"), borderPadding=5,
                          borderColor=colors.HexColor("#E69F00"), borderWidth=0.8, spaceBefore=4, spaceAfter=8)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm,
                            bottomMargin=14 * mm, title="AirframeSelect report", author="AirframeSelect")
    story: list[Any] = [
        Paragraph("AirframeSelect: material recommendation report", h1),
        Paragraph(f"Generated {date.today().isoformat()} by AirframeSelect {__version__}", small),
        Paragraph(DISCLAIMER, warn),
    ]
    # Inputs
    story.append(Paragraph("1. Inputs", h2))
    cons = inp["constraints"]
    cons_txt = "; ".join(f"{k}: {'none' if v is None else v}" for k, v in cons.items())
    story.append(Paragraph(f"<b>Part:</b> {inp['part']['name']} &nbsp; <b>Mission profile:</b> {inp['profile']['name']} "
                           f"&nbsp; <b>Method:</b> {inp['method'].upper()}", body))
    story.append(Paragraph(f"<b>Load case:</b> {inp['part']['load_case']}", body))
    story.append(Paragraph(f"<b>Performance index:</b> {inp['performance_index']['label']} "
                           f"({inp['performance_index']['formula']}, units {inp['performance_index']['units']})", body))
    story.append(Paragraph(f"<b>Why this index:</b> {inp['part']['rationale']}", body))
    story.append(Paragraph(f"<b>Hard constraints:</b> {cons_txt}", body))
    labels = {c["key"]: c["label"] for c in load_presets()["criteria"]}
    wt = Table([[labels[c] for c in CRITERIA], [f"{inp['weights'][c]*100:.1f}%" for c in CRITERIA]])
    wt.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF4"))]))
    story += [Spacer(1, 4), Paragraph("<b>Criteria weights (normalised):</b>", body), wt]
    # Ranking table
    story.append(Paragraph(f"2. Ranking ({ranking['n_candidates']} candidates of {ranking['n_total']})", h2))
    if not ranking["ranking"]:
        story.append(Paragraph(ranking.get("message") or "No candidates.", body))
    else:
        rob = {m["id"]: m for m in robustness.get("materials", [])}
        data = [["#", "Material", "Score", "P(#1)", "P(top 3)", "Confidence", "Flags"]]
        for r in ranking["ranking"][:15]:
            m = rob.get(r["id"], {})
            data.append([r["rank"], Paragraph(r["name"], small), f"{r['score']:.3f}",
                         f"{m['p_rank1']*100:.0f}%" if m else "-", f"{m['p_top3']*100:.0f}%" if m else "-",
                         m.get("confidence", "-"), Paragraph(", ".join(r["flags"]) or "-", small)])
        t = Table(data, colWidths=[8 * mm, 62 * mm, 16 * mm, 15 * mm, 17 * mm, 21 * mm, 41 * mm], repeatRows=1)
        t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF4")),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(t)
        ag = ranking["agreement"]
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"TOPSIS and weighted sum {'agree' if ag['top3_agree'] else 'do not fully agree'} on the top 3 "
            f"(overlap {ag['top3_overlap']} of {min(3, len(ranking['ranking']))}); rank correlation (Spearman) {ag['spearman']:.2f}. "
            f"The table is ordered by {inp['method'].upper()}.", body))
        # Robustness
        story.append(Paragraph("3. Robustness summary", h2))
        s = robustness.get("settings", {})
        conc = s.get("concentration")
        story.append(Paragraph(
            f"{s.get('trials')} Monte Carlo trials (seed {s.get('seed')}); weights drawn from a Dirichlet distribution "
            f"({'fixed weights' if conc is None else 'concentration ' + format(conc, 'g')}), properties sampled uniformly within their ranges "
            f"(range scale {s.get('range_scale')}). {robustness.get('summary', '')}", body))
        top = robustness["materials"][:8]
        story += [Spacer(1, 3), Paragraph("Probability of being in the top 3:", small),
                  _bar_table([(m["name"][:34], m["p_top3"]) for m in top])]
        # Explanation
        story.append(Paragraph("4. Why these materials?", h2))
        for r in ranking["ranking"][:3]:
            story.append(Paragraph(f"<b>#{r['rank']}</b> {r['explanation']}", body))
            if r.get("caveat"):
                story.append(Paragraph(f"Caveat: {r['caveat']}", small))
    story.append(Paragraph("5. Assumptions", h2))
    for a in ASSUMPTIONS:
        story.append(Paragraph("- " + a, small))
    story.append(Paragraph("6. Data verification", h2))
    story.append(Paragraph(DISCLAIMER, small))
    story.append(Paragraph(load_materials_doc()["disclaimer"], small))
    doc.build(story)
    return buf.getvalue()
