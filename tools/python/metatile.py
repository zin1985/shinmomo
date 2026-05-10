#!/usr/bin/env python3
"""2x2 metatile reconstruction skeleton from tilemap_world.csv."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilemap", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    Path(args.out).write_text(
        "frame,world_x,world_y,tiles_2x2,metatile_id,confidence,note\n"
        "TODO,TODO,TODO,TODO,TODO,TODO,derive after stabilization interval\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
