#!/usr/bin/env python3
"""Extract minimal Goal13 bridge rows from runtime summaries.

This is a schema-first stub. It intentionally does not read ROM binaries.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", required=True, help="frame.csv")
    ap.add_argument("--visible", required=True, help="visible.csv")
    ap.add_argument("--out", required=True, help="g13_mask_minimal.csv")
    args = ap.parse_args()

    frame_path = Path(args.frame)
    visible_path = Path(args.visible)
    out_path = Path(args.out)

    if not frame_path.exists() or not visible_path.exists():
        raise SystemExit("input CSV missing")

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["execution_frame", "cutoff_index", "rank", "termination_flag", "note"])
        w.writerow(["TODO", "TODO", "TODO", "TODO", "fill from runtime summaries"])


if __name__ == "__main__":
    main()
