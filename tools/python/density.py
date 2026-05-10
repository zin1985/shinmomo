#!/usr/bin/env python3
"""Compute density/accumulation placeholders from visible summaries."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visible", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    counts: dict[str, int] = defaultdict(int)
    with Path(args.visible).open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            counts[row.get("frame", "")] += 1

    with Path(args.out).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame", "visible_count", "density_acceleration", "accumulated_acceleration", "note"])
        for frame, count in sorted(counts.items()):
            w.writerow([frame, count, "TODO", "TODO", "derive from ranked contribution estimates"])


if __name__ == "__main__":
    main()
