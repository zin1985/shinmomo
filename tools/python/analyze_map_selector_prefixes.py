#!/usr/bin/env python3
"""Conservative prefix decoder for unresolved record0/entry1 map selectors.

This tool never guesses unknown VM lengths. It starts from the proven state-0
entry1 substream and advances only across opcodes whose normal-mode length is
independently proven from the C4 handler/pointer-advance logic.

Any unknown opcode, unresolved prior 0x50, or 0x51 stops the walk.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

SAFE_LENGTHS = {
    0x04: 2,  # proven pack switch; does not itself change $1398/$1399
    0x08: 4,
    0x10: 2,
    0x11: 2,
    0x13: 2,
    0x15: 3,
    0x2D: 2,
    0x33: 4,
    0x96: 2,
}


def file_off(cpu: str) -> int:
    bank_s, addr_s = cpu.split(":")
    return ((int(bank_s, 16) - 0xC0) << 16) | int(addr_s, 16)


def cpu_addr(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--catalog",
        type=Path,
        default=Path("data/maps/selectors/primary_map_selector_catalog.csv"),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/maps/selectors/record0_entry1_prefix_analysis.csv"),
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=Path("data/maps/selectors/record0_entry1_prefix_summary.json"),
    )
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit("unexpected ROM identity")

    with args.catalog.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    by_addr = {file_off(r["command_addr"]): r for r in rows}
    targets = [
        r for r in rows
        if r["normal_mode_confirmed"].lower() == "false"
        and int(r["record_index"]) == 0
        and int(r["entry_id_dec"]) == 1
    ]

    out = []
    status_counts = Counter()
    reached_sequences = Counter()

    for row in targets:
        start = file_off(row["substream_start"])
        target = file_off(row["command_addr"])
        p = start
        decoded = []
        status = "reached_target"

        while p < target:
            op = rom[p]

            if op == 0x50:
                prior = by_addr.get(p)
                if prior and prior["normal_mode_confirmed"].lower() == "true":
                    decoded.append((op, 4))
                    p += 4
                    continue
                status = "blocked_unresolved_prior_50"
                break

            if op == 0x51:
                status = "blocked_51"
                break

            length = SAFE_LENGTHS.get(op)
            if length is None:
                status = f"blocked_unknown_{op:02X}"
                break

            if p + length > target:
                status = "blocked_overrun"
                break

            decoded.append((op, length))
            p += length

        if p != target and status == "reached_target":
            status = "blocked_misaligned"

        status_counts[status] += 1
        seq = " ".join(f"{op:02X}" for op, _ in decoded)
        if status == "reached_target":
            reached_sequences[seq] += 1

        out.append(
            {
                "pack_id_hex": row["pack_id_hex"],
                "record_index": row["record_index"],
                "entry_id_hex": row["entry_id_hex"],
                "substream_start": row["substream_start"],
                "target_50": row["command_addr"],
                "target_tileset_id": row["primary_tileset_id"],
                "target_layout_id": row["primary_layout_id"],
                "target_variant": row["map_variant"],
                "prefix_bytes": target - start,
                "decode_status": status,
                "stop_addr": cpu_addr(p),
                "stop_byte": f"0x{rom[p]:02X}" if p < target else "",
                "decoded_opcode_sequence": seq,
                "decoded_opcode_count": len(decoded),
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    summary = {
        "schema_version": 1,
        "kind": "record0_entry1_selector_prefix_analysis",
        "rom_sha256": sha,
        "target_count": len(targets),
        "safe_length_opcodes": {
            f"0x{k:02X}": v for k, v in sorted(SAFE_LENGTHS.items())
        },
        "status_counts": dict(sorted(status_counts.items())),
        "reached_target_count": status_counts["reached_target"],
        "reached_target_distinct_packs": len(
            {r["pack_id_hex"] for r in out if r["decode_status"] == "reached_target"}
        ),
        "reached_opcode_sequences": [
            {"sequence": seq, "count": count}
            for seq, count in reached_sequences.most_common()
        ],
        "promotion_policy": (
            "reached_target is structural prefix alignment only. Do not promote "
            "to confirmed normal mode until every decoded handler/callee is "
            "cleared for $1398/$1399 mutation or C0:C9E7 re-entry."
        ),
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
