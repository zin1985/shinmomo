#!/usr/bin/env python3
"""Catalog high-confidence Shinmomo keyed-dispatch tables.

The generic matcher at C4:8699 scans:
    [key:1][target16:2] ... [00]

This tool intentionally uses conservative structural anchors. A table is emitted
only when:
- a 09 <ptr24> occurrence inside a real CA script pack points inside that pack;
- the pointed bytes parse as >=2 key/target records followed by key 0;
- every target stays inside the same pack; and
- at least one target starts with 09 <the same table pointer>.

That self-reference criterion filters incidental byte triples and identifies
state-machine-like script tables without claiming game-facing key semantics.
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
CA_BOUNDARY_OFFSET = 0x0AC000
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9
FINAL_SENTINEL_INDEX = 0xFA


def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | addr


def cpu_from_file(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def read_ca_boundaries(rom: bytes) -> list[dict]:
    rows = []
    for idx in range(FINAL_SENTINEL_INDEX + 1):
        off = CA_BOUNDARY_OFFSET + idx * 3
        lo, hi, bank = rom[off:off + 3]
        addr = lo | (hi << 8)
        rows.append({
            "index": idx,
            "bank": bank,
            "addr": addr,
            "file": file_from_cpu(bank, addr),
        })
    return rows


def parse_table(rom: bytes, pack_start: int, pack_end: int,
                table_off: int, max_records: int = 16):
    bank = 0xC0 + (table_off >> 16)
    p = table_off
    rows = []
    for _ in range(max_records):
        if p >= pack_end:
            return None
        key = rom[p]
        if key == 0:
            return rows if len(rows) >= 2 else None
        if p + 2 >= pack_end:
            return None
        target16 = rom[p + 1] | (rom[p + 2] << 8)
        target = ((bank - 0xC0) << 16) | target16
        if not (pack_start <= target < pack_end):
            return None
        rows.append((key, target))
        p += 3
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("data/events"))
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM SHA-256: {sha}")

    ca = read_ca_boundaries(rom)
    tables = {}
    references = Counter()

    for family in range(FIRST_REAL_PACK, LAST_REAL_PACK + 1):
        start = ca[family]["file"]
        end = ca[family + 1]["file"]
        bank = ca[family]["bank"]
        seen = set()

        for call in range(start, max(start, end - 3)):
            if rom[call] != 0x09:
                continue
            lo, hi, ptr_bank = rom[call + 1:call + 4]
            if ptr_bank != bank:
                continue
            table_off = file_from_cpu(ptr_bank, lo | (hi << 8))
            if not (start <= table_off < end):
                continue
            rows = parse_table(rom, start, end, table_off)
            if rows is None:
                continue

            ptr_bytes = bytes([0x09, lo, hi, ptr_bank])
            self_refs = sum(
                rom[target:target + 4] == ptr_bytes
                for _, target in rows
            )
            if self_refs == 0:
                continue

            key = (family, table_off)
            references[key] += 1
            if table_off in seen:
                continue
            seen.add(table_off)
            tables[key] = {
                "rows": rows,
                "self_refs": self_refs,
            }

    args.out_dir.mkdir(parents=True, exist_ok=True)

    table_rows = []
    target_rows = []
    key_counts = Counter()
    a4_pairs = set()
    pair_6c_7b = 0
    key_7b_self_set80 = 0
    key_6c_self_controller_create = 0

    for (family, table_off), info in sorted(tables.items()):
        rows = info["rows"]
        keys = [key for key, _ in rows]
        if 0x6C in keys and 0x7B in keys:
            pair_6c_7b += 1

        table_rows.append({
            "family_id": family,
            "family_hex": f"0x{family:02X}",
            "table_cpu": cpu_from_file(table_off),
            "record_count": len(rows),
            "reference_09_count": references[(family, table_off)],
            "self_reference_targets": info["self_refs"],
            "keys_hex": ";".join(f"0x{k:02X}" for k in keys),
            "evidence_class": "strong_keyed_dispatch_table",
        })

        bank = 0xC0 + (table_off >> 16)
        ptr_bytes = bytes([
            0x09,
            table_off & 0xFF,
            (table_off >> 8) & 0xFF,
            bank,
        ])

        for ordinal, (key, target) in enumerate(rows):
            key_counts[key] += 1
            prefix = rom[target:target + 8]
            self_ref = rom[target:target + 4] == ptr_bytes
            a4_subindex = ""
            if rom[target] == 0xA4:
                a4_subindex = f"0x{rom[target + 1]:02X}"
                a4_pairs.add((family, rom[target + 1], target))

            if key == 0x7B and self_ref and len(prefix) >= 7:
                if prefix[4:7] == bytes([0x16, 0x00, 0x80]):
                    key_7b_self_set80 += 1
            if key == 0x6C and self_ref and len(prefix) >= 5:
                if prefix[4] == 0x59:
                    key_6c_self_controller_create += 1

            target_rows.append({
                "family_id": family,
                "family_hex": f"0x{family:02X}",
                "table_cpu": cpu_from_file(table_off),
                "ordinal": ordinal,
                "key": key,
                "key_hex": f"0x{key:02X}",
                "target_cpu": cpu_from_file(target),
                "target_first_opcode": f"0x{rom[target]:02X}",
                "self_reference_target": int(self_ref),
                "a4_subindex": a4_subindex,
                "evidence_class": "keyed_dispatch_target",
            })

    with (args.out_dir / "keyed_dispatch_table_catalog.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(table_rows[0].keys()))
        w.writeheader()
        w.writerows(table_rows)

    with (args.out_dir / "keyed_dispatch_target_catalog.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(target_rows[0].keys()))
        w.writeheader()
        w.writerows(target_rows)

    summary = {
        "rom_sha256": sha,
        "high_confidence_tables": len(table_rows),
        "families_with_tables": len({r["family_id"] for r in table_rows}),
        "key_target_records": len(target_rows),
        "self_reference_targets": sum(r["self_reference_target"] for r in target_rows),
        "unique_keys": len(key_counts),
        "most_common_keys": [
            {"key": f"0x{k:02X}", "count": v}
            for k, v in key_counts.most_common(16)
        ],
        "tables_with_both_0x6C_and_0x7B": pair_6c_7b,
        "key_0x7B_selfref_targets_setting_entity_flag_0x80": key_7b_self_set80,
        "key_0x6C_selfref_targets_starting_controller_create_0x59": key_6c_self_controller_create,
        "a4_target_callsites": len(a4_pairs),
        "a4_target_unique_pairs": len({(f, s) for f, s, _ in a4_pairs}),
        "interpretation": (
            "C4:8699-compatible keyed state-machine tables with internal "
            "self-reference evidence; key names remain semantic hypotheses"
        ),
    }
    (args.out_dir / "keyed_dispatch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
