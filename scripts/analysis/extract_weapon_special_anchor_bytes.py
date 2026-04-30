#!/usr/bin/env python3
"""
Extract short byte anchors for Shin Momotarou Densetsu weapon-special investigation.

Usage:
  python scripts/analysis/extract_weapon_special_anchor_bytes.py "/path/to/Shin Momotarou Densetsu (J).smc"

ROM is not included in this repository/package.
"""
from __future__ import annotations
from pathlib import Path
import csv
import sys

ANCHORS = [
    ("weapon_special_pointer_table_start", 0x0B01F9, 64),
    ("weapon_special_core_script_header", 0x0B03D1, 64),
    ("op83_default_body", 0x0B03E1, 64),
    ("fallback_executor_op82_default", 0x0B0408, 64),
    ("selector_dispatch_candidate_A_CA_D800_raw", 0x0AD800, 64),
    ("selector_dispatch_candidate_B_CB_D800_raw", 0x0BD800, 64),
]

def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: extract_weapon_special_anchor_bytes.py ROM.smc", file=sys.stderr)
        return 2
    rom_path = Path(sys.argv[1])
    data = rom_path.read_bytes()
    rows = []
    for label, off, length in ANCHORS:
        if off + length > len(data):
            raise ValueError(f"Anchor {label} exceeds ROM size")
        rows.append({
            "label": label,
            "raw_offset_hex": f"0x{off:06X}",
            "length": length,
            "hex_bytes": data[off:off+length].hex(" "),
        })
    out = Path("weapon_special_anchor_bytes.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "raw_offset_hex", "length", "hex_bytes"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
