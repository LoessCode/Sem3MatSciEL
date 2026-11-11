"""Command-line interface: python -m airframeselect rank --part arm --profile balanced."""
from __future__ import annotations

import argparse
import json
import sys

from .data import load_presets
from .pipeline import InputError, run_ranking, run_robustness


def _build_parser() -> argparse.ArgumentParser:
    presets = load_presets()
    parts = [p["id"] for p in presets["parts"]]
    profiles = [p["id"] for p in presets["profiles"]]
    ap = argparse.ArgumentParser(prog="airframeselect", description="Material selection for UAV airframe parts.")
    sub = ap.add_subparsers(dest="command", required=True)
    rk = sub.add_parser("rank", help="Rank materials for a part and mission profile")
    rk.add_argument("--part", required=True, choices=parts)
    rk.add_argument("--profile", default="balanced", choices=profiles)
    rk.add_argument("--method", default="topsis", choices=["topsis", "wsm"])
    rk.add_argument("--top", type=int, default=10, help="number of rows to show (default 10)")
    rk.add_argument("--robustness", action="store_true", help="add Monte Carlo confidence columns")
    rk.add_argument("--trials", type=int, default=2000)
    rk.add_argument("--seed", type=int, default=42)
    rk.add_argument("--json", action="store_true", help="print the full result as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = run_ranking(args.part, args.profile, method=args.method)
        rob = run_robustness(args.part, args.profile, method=args.method, trials=args.trials, seed=args.seed) if args.robustness else None
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"ranking": result, "robustness": rob}, indent=2))
        return 0
    inp = result["inputs"]
    print(f"Part: {inp['part']['name']}   Profile: {inp['profile']['name']}   Method: {args.method.upper()}")
    print(f"Performance index: {inp['performance_index']['label']} ({inp['performance_index']['formula']})")
    print(f"Candidates: {result['n_candidates']} of {result['n_total']} (others excluded by constraints)")
    if result["message"]:
        print(result["message"])
        return 0
    rob_by_id = {m["id"]: m for m in rob["materials"]} if rob else {}
    header = f"{'#':>2}  {'Material':<40} {'Score':>6}"
    if rob:
        header += f"  {'P(#1)':>6} {'P(top3)':>7}  Confidence"
    print(header)
    for row in result["ranking"][: args.top]:
        line = f"{row['rank']:>2}  {row['name']:<40} {row['score']:>6.3f}"
        if rob:
            m = rob_by_id[row["id"]]
            line += f"  {m['p_rank1']*100:5.1f}% {m['p_top3']*100:6.1f}%  {m['confidence']}"
        print(line)
    print()
    print(result["ranking"][0]["explanation"])
    ag = result["agreement"]
    print(f"TOPSIS vs weighted sum: top-3 {'agree' if ag['top3_agree'] else 'differ'} (overlap {ag['top3_overlap']}/3), Spearman {ag['spearman']:.2f}")
    print("Note: material values are typical figures that need verification against datasheets.")
    return 0
