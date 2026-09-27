#!/usr/bin/env python3
"""Summarize map/tilemap evidence from one or more raw VRAM captures.

Raw VRAM stays outside Git. This tool emits only derived metadata:
- whole-capture SHA-256;
- per-page SHA-256;
- structural tilemap metrics;
- byte-diff counts against the first capture.

Example:
  python tools/python/summarize_tilemap_evidence.py \
    --capture older=C:\\...\\vram.bin \
    --capture fresh=C:\\...\\vram.bin \
    --pages 0x1000 0x1800 0xA000 0xC000 \
    --out evidence.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rank_vram_tilemap_pages import decode_page, page_metrics


def parse_page(value: str) -> int:
    page = int(value, 0)
    if page < 0 or page > 0xF800 or page % 0x800:
        raise argparse.ArgumentTypeError("page must be a 0x800-aligned VRAM base in 0x0000..0xF800")
    return page


def parse_capture(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("capture must be LABEL=PATH")
    label, raw_path = value.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("capture label must not be empty")
    return label, Path(raw_path)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="append", required=True, type=parse_capture)
    ap.add_argument("--pages", nargs="+", required=True, type=parse_page)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    captures: list[tuple[str, bytes]] = []
    for label, path in args.capture:
        data = path.read_bytes()
        if len(data) != 0x10000:
            raise SystemExit(f"{label}: expected 65536-byte VRAM dump, got {len(data)}")
        captures.append((label, data))

    baseline_label, baseline = captures[0]
    payload: dict = {
        "schema_version": 1,
        "kind": "derived_vram_tilemap_evidence",
        "baseline_capture": baseline_label,
        "captures": [],
        "pages": [],
        "policy": "Raw VRAM is intentionally omitted; this file contains hashes, counts and structural metrics only.",
    }

    for label, data in captures:
        payload["captures"].append({
            "label": label,
            "vram_sha256": sha256(data),
            "byte_diffs_vs_baseline": sum(a != b for a, b in zip(baseline, data)),
        })

    for page in args.pages:
        row = {
            "page_base": f"0x{page:04X}",
            "captures": [],
        }
        base_page = baseline[page:page + 0x800]
        for label, data in captures:
            raw = data[page:page + 0x800]
            metrics = page_metrics(decode_page(data, page))
            row["captures"].append({
                "label": label,
                "page_sha256": sha256(raw),
                "byte_diffs_vs_baseline": sum(a != b for a, b in zip(base_page, raw)),
                "unique_entries": metrics["unique_entries"],
                "unique_tiles": metrics["unique_tiles"],
                "unique_metatiles_2x2": metrics["unique_metatiles_2x2"],
                "metatile_repeat_ratio": round(metrics["metatile_repeat_ratio"], 6),
                "dominant_palette_ratio": round(metrics["dominant_palette_ratio"], 6),
                "priority_1_ratio": round(metrics["priority_1_ratio"], 6),
                "zero_entry_ratio": round(metrics["zero_entry_ratio"], 6),
                "structural_score": round(metrics["score"], 6),
            })
        payload["pages"].append(row)

    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
