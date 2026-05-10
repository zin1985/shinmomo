#!/usr/bin/env python3
"""Cluster tracking skeleton for summarized OAM rows."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oam", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    Path(args.out).write_text(
        "frame,cluster_track_id,oam_ids,chr_ids,stable,fragmented,note\n"
        "TODO,TODO,TODO,TODO,TODO,TODO,derive stable logical IDs from OAM continuity\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
