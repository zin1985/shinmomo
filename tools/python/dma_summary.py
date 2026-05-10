#!/usr/bin/env python3
"""DMA summary skeleton. Keeps only summarized rows, not raw dumps."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    Path(args.out).write_text(
        "frame,channel,source,dest,size,kind,note\n"
        "TODO,TODO,TODO,TODO,TODO,TODO,presentation-only summary for Goal13\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
