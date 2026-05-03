#!/usr/bin/env python3
"""
Generate recompilable C initializers from a local Shin Momotarou Densetsu ROM.

This tool intentionally does not ship or require distributing the ROM.
It emits C data for the currently known tables only.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import csv

def u16le(bs: bytes) -> int:
    return bs[0] | (bs[1] << 8)

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def branch_records(rom: bytes, start: int = 0x41A10, count: int = 160):
    for i in range(count):
        off = start + i * 8
        bs = rom[off:off+8]
        if len(bs) < 8:
            break
        target = u16le(bs[6:8])
        yield off, bs, target

def macro_rows(rom: bytes, start: int, count: int = 64):
    for i in range(count):
        off = start + i * 9
        bs = rom[off:off+9]
        if len(bs) < 9:
            break
        yield off, bs, u16le(bs[7:9])

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path, default=Path("recompilable_c/generated"))
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    branch_csv = out / "branch_41A10.csv"
    with branch_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index","rom_offset","key","c1","c2","c3","c4","c5","target","target_rom_offset","raw_hex"])
        for i, (off, bs, target) in enumerate(branch_records(rom)):
            w.writerow([i, f"0x{off:06X}", *[f"0x{x:02X}" for x in bs[:6]], f"0x{target:04X}", f"0x{0x30000+target:06X}", bs.hex().upper()])

    macro_csv = out / "macro_rows_398xx.csv"
    with macro_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["family","index","rom_offset","label_word","label_file_guess","raw_hex"])
        for fam, start in [("A_39847", 0x39847), ("B_39916", 0x39916)]:
            for i, (off, bs, label) in enumerate(macro_rows(rom, start)):
                label_file = 0x30000 + label if label >= 0x8000 else label
                w.writerow([fam, i, f"0x{off:06X}", f"0x{label:04X}", f"0x{label_file:06X}", bs.hex().upper()])

    print(f"wrote {branch_csv}")
    print(f"wrote {macro_csv}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
