#!/usr/bin/env python3
"""Filter Goal13 bridge rows by execution_frame/cutoff_index.

No ROM access. Designed for summarized CSVs only.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--execution-frame")
    ap.add_argument("--cutoff-index")
    args = ap.parse_args()

    in_path = Path(args.infile)
    out_path = Path(args.out)

    with in_path.open("r", newline="", encoding="utf-8") as src, out_path.open("w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row in reader:
            if args.execution_frame and row.get("execution_frame") != args.execution_frame:
                continue
            if args.cutoff_index and row.get("cutoff_index") != args.cutoff_index:
                continue
            writer.writerow(row)


if __name__ == "__main__":
    main()
