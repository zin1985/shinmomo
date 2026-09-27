#!/usr/bin/env python3
"""Catalog the CA:C2F4 per-pack seed table and join seeds to script records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
MASTER = 0x0AC000
SEED_TABLE = 0x0AC2F4
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9


def off(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | addr


def cpu(o: int) -> str:
    return f"{0xC0 + (o >> 16):02X}:{o & 0xFFFF:04X}"


def root(rom: bytes, pack_id: int) -> int:
    o = MASTER + pack_id * 3
    lo, hi, bank = rom[o:o + 3]
    return off(bank, lo | (hi << 8))


def records_for_pack(rom: bytes, pack_id: int) -> list[tuple[int, int]]:
    start = root(rom, pack_id)
    end = root(rom, pack_id + 1)
    bank = 0xC0 + (start >> 16)
    addr = start & 0xFFFF
    first16 = rom[start] | (rom[start + 1] << 8)
    first_bank = bank + (1 if first16 < addr else 0)
    first = off(first_bank, first16)
    count = (first - start - 4) // 2
    vals = [
        rom[start + 2 * i] | (rom[start + 2 * i + 1] << 8)
        for i in range(count)
    ]
    trailer = rom[start + count * 2:start + count * 2 + 4]
    if trailer != bytes([0, 0, 0, pack_id]):
        raise SystemExit(f"bad pack trailer 0x{pack_id:02X}")

    ptrs = []
    current_bank = bank
    for i, value in enumerate(vals):
        if (i == 0 and value < addr) or (i and value < vals[i - 1]):
            current_bank += 1
        ptrs.append(off(current_bank, value))

    return [
        (p, ptrs[i + 1] if i + 1 < len(ptrs) else end)
        for i, p in enumerate(ptrs)
    ]


def record_entries(rom: bytes, start: int, end: int) -> list[tuple[int, int, int]]:
    p = start
    entries: list[tuple[int, int]] = []
    for _ in range(128):
        if p >= end:
            return []
        tag = rom[p]
        if tag == 0:
            if not entries:
                return []
            out = []
            for i, (entry_id, entry_start) in enumerate(entries):
                entry_end = entries[i + 1][1] if i + 1 < len(entries) else end
                out.append((entry_id, entry_start, entry_end))
            return out
        ptr16 = rom[p + 1] | (rom[p + 2] << 8)
        bank = 0xC0 + (start >> 16)
        target = off(bank, ptr16)
        while target < start:
            target += 0x10000
        entries.append((tag, target))
        p += 3
    return []


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/maps/selectors"),
    )
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit("canonical ROM verification failed")

    # Table is self-delimiting: entry for pack 0x14 is the first non-zero
    # pointer, and points exactly 500 bytes after CA:C2F4.
    first_data = rom[SEED_TABLE + 2 * (FIRST_REAL_PACK - 1)]
    first_data |= rom[SEED_TABLE + 2 * (FIRST_REAL_PACK - 1) + 1] << 8
    table_count = (first_data - 0xC2F4) // 2
    if table_count != 250 or first_data != 0xC4E8:
        raise SystemExit(
            f"unexpected seed table boundary: count={table_count}, "
            f"first=0x{first_data:04X}"
        )

    list_ptrs = [
        rom[SEED_TABLE + 2 * i] | (rom[SEED_TABLE + 2 * i + 1] << 8)
        for i in range(table_count)
    ]
    if any(list_ptrs[i] != 0 for i in range(FIRST_REAL_PACK - 1)):
        raise SystemExit("reserved seed-table ids 1..0x13 are not all zero")

    rows = []
    malformed_lists = 0
    pack_mismatches = 0
    nonempty_packs = set()

    for index, list_ptr16 in enumerate(list_ptrs):
        pack_id = index + 1
        if list_ptr16 == 0:
            continue

        q = off(0xCA, list_ptr16)
        list_end = q
        seed_index = 0
        while True:
            value = rom[list_end]
            value |= rom[list_end + 1] << 8
            value |= rom[list_end + 2] << 16
            list_end += 3
            if value == 0:
                break

            seed_index += 1
            seed = off((value >> 16) & 0xFF, value & 0xFFFF)
            if pack_id <= LAST_REAL_PACK:
                ps = root(rom, pack_id)
                pe = root(rom, pack_id + 1)
                if not (ps <= seed < pe):
                    pack_mismatches += 1

            record_index = ""
            entry_id = ""
            relation = "unresolved"
            if pack_id <= LAST_REAL_PACK:
                for ri, (rs, re) in enumerate(records_for_pack(rom, pack_id)):
                    if not (rs <= seed < re):
                        continue
                    record_index = ri
                    for tag, st, en in record_entries(rom, rs, re):
                        if st <= seed < en:
                            entry_id = f"0x{tag:02X}"
                            relation = (
                                "substream_start" if seed == st else "inside_substream"
                            )
                            break
                    if relation == "unresolved" and seed == rs:
                        relation = "record_start"
                    break

            if seed_index:
                nonempty_packs.add(pack_id)
            rows.append(
                {
                    "pack_id_dec": pack_id,
                    "pack_id_hex": f"0x{pack_id:02X}",
                    "list_pointer": f"CA:{list_ptr16:04X}",
                    "seed_index": seed_index,
                    "seed_script_addr": cpu(seed),
                    "record_index": record_index,
                    "entry_id": entry_id,
                    "relation": relation,
                }
            )

        # Next non-zero list pointer must begin exactly after this list's zero.
        next_ptr = None
        for j in range(index + 1, table_count):
            if list_ptrs[j]:
                next_ptr = off(0xCA, list_ptrs[j])
                break
        if next_ptr is not None and list_end != next_ptr:
            malformed_lists += 1

    summary = {
        "schema_version": 1,
        "kind": "per_pack_entry79_seed_index",
        "rom_sha256": sha,
        "table_addr": "CA:C2F4",
        "table_entry_count": table_count,
        "first_data_addr": "CA:C4E8",
        "reserved_null_ids": "0x01..0x13",
        "nonzero_list_pointer_count": sum(1 for x in list_ptrs if x),
        "nonempty_seed_pack_count": len(nonempty_packs),
        "seed_script_count": len(rows),
        "malformed_list_count": malformed_lists,
        "pack_interval_mismatch_count": pack_mismatches,
        "substream_start_count": sum(
            1 for row in rows if row["relation"] == "substream_start"
        ),
        "entry_id_counts": {
            key: sum(1 for row in rows if row["entry_id"] == key)
            for key in sorted({row["entry_id"] for row in rows})
        },
        "interpretation": (
            "$0305 indexes this table as pack_id-1. Every one of the 90 "
            "non-zero seed scripts is inside the same-numbered CA:C000 pack "
            "and is exactly the start of entry_id 0x79."
        ),
    }

    if malformed_lists or pack_mismatches:
        raise SystemExit("seed table structural verification failed")
    if len(rows) != 90:
        raise SystemExit(f"unexpected seed count: {len(rows)}")
    if any(row["relation"] != "substream_start" for row in rows):
        raise SystemExit("not every seed resolves to a substream start")
    if any(row["entry_id"] != "0x79" for row in rows):
        raise SystemExit("not every seed resolves to entry 0x79")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "map_pack_entry79_seed_catalog.csv", rows)
    (args.out_dir / "map_pack_entry79_seed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
