#!/usr/bin/env python3
"""
Export candidate VM blobs as a neutral ShinVM DSL.

The DSL is deliberately conservative. Unknown bytes stay as BYTE directives.
"""

from __future__ import annotations
import argparse
from pathlib import Path

def export_blob(name: str, bs: bytes, base: int) -> str:
    out = [f"blob {name} @0x{base:06X} {{"]
    pc = 0
    while pc < len(bs):
        op = bs[pc]
        if op == 0x00:
            out.append(f"  0x{pc:04X}: END")
            pc += 1
        elif op == 0x07 and pc + 2 < len(bs):
            out.append(f"  0x{pc:04X}: COMMAND 0x{bs[pc+1]:02X} 0x{bs[pc+2]:02X}")
            pc += 3
        elif op in (0x80, 0xFF) and pc + 1 < len(bs):
            out.append(f"  0x{pc:04X}: BRANCH_LIKE 0x{op:02X} 0x{bs[pc+1]:02X}")
            pc += 2
        else:
            out.append(f"  0x{pc:04X}: BYTE 0x{op:02X}")
            pc += 1
    out.append("}")
    return "\\n".join(out)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path, default=Path("dsl"))
    ap.add_argument("--length", type=int, default=128)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    args.out.mkdir(parents=True, exist_ok=True)

    for name, off in [("F09A_candidate", 0x03F09A), ("F0DB_candidate", 0x03F0DB), ("F0C6_candidate", 0x03F0C6)]:
        bs = rom[off:off+args.length]
        (args.out / f"{name}.shinvm").write_text(export_blob(name, bs, off), encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
