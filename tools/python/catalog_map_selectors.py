#!/usr/bin/env python3
"""Catalog structurally bounded Shinmomo map-selector candidates.

This parser is intentionally conservative.

It uses the CA:C000 master pack table and same-bank pack-local record pointer
tables to reproduce the 4,092-record corpus used by the map-selector analysis.
Within records that expose the proven entry/substream header grammar,

    [entry_id:1][substream_ptr16:2] ... 00

it catalogs normal-map-shaped opcode 0x50 commands whose operands satisfy the
ROM-side map-loader table cardinalities and the confirmed $139B variant range.

Important: opcode >= 0x50 is dispatched through a different bank-82 table when
$1398 != 0. Therefore rows outside the already confirmed setup signature remain
"structurally strong candidates", not unconditional runtime semantics.

No ROM payload or decoded map grid is written.
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

CA_TABLE_FILE = 0x0AC000
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9

# Four real packs cross a bank boundary and require a separate parser.
KNOWN_CROSS_BANK_PACKS = {0x15, 0x48, 0x9E, 0xF2}

# Family 0x14 record 0 is a large pointer/table blob, not a VM record.
EXCLUDED_NON_VM_RECORDS = {(0x14, 0)}

CONFIRMED_SETUP_SIGNATURE = bytes.fromhex("10 0A 10 0B 11 09")


def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | (addr & 0xFFFF)


def cpu_from_file(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def u16_file(rom: bytes, off: int) -> int:
    return rom[off] | (rom[off + 1] << 8)


def u24_file(rom: bytes, off: int) -> int:
    return rom[off] | (rom[off + 1] << 8) | (rom[off + 2] << 16)


def read_pack_root(rom: bytes, pack_id: int) -> tuple[int, int, int]:
    off = CA_TABLE_FILE + pack_id * 3
    lo, hi, bank = rom[off : off + 3]
    addr = lo | (hi << 8)
    return bank, addr, file_from_cpu(bank, addr)


def parse_same_bank_pack(rom: bytes, pack_id: int) -> dict | None:
    bank, addr, start = read_pack_root(rom, pack_id)
    next_bank, next_addr, end = read_pack_root(rom, pack_id + 1)
    if bank != next_bank:
        return None

    first_ptr16 = u16_file(rom, start)
    first = file_from_cpu(bank, first_ptr16)
    if first < start:
        first += 0x10000

    delta = first - start
    if delta < 4 or (delta - 4) % 2:
        return None
    count = (delta - 4) // 2
    if count <= 0:
        return None

    ptr16s = [u16_file(rom, start + 2 * i) for i in range(count)]
    if any(ptr16s[i] >= ptr16s[i + 1] for i in range(len(ptr16s) - 1)):
        return None
    if any(p < addr for p in ptr16s):
        return None

    trailer = rom[start + count * 2 : start + count * 2 + 4]
    if trailer != bytes([0x00, 0x00, 0x00, pack_id]):
        return None

    ptrs = [file_from_cpu(bank, p) for p in ptr16s]
    if ptrs[0] != first or not all(start < p < end for p in ptrs):
        return None

    records = []
    for record_index, record_start in enumerate(ptrs):
        record_end = ptrs[record_index + 1] if record_index + 1 < len(ptrs) else end
        records.append(
            {
                "pack_id": pack_id,
                "record_index": record_index,
                "start": record_start,
                "end": record_end,
            }
        )

    return {
        "pack_id": pack_id,
        "bank": bank,
        "start": start,
        "end": end,
        "records": records,
    }


def parse_record_header(rom: bytes, record: dict) -> dict | None:
    """Parse [entry_id][ptr16]...00 and require ordered in-record targets."""
    start = record["start"]
    end = record["end"]
    p = start
    entries = []

    while p < end and len(entries) < 128:
        entry_id = rom[p]
        if entry_id == 0:
            header_end = p + 1
            if not entries:
                return None
            targets = [e["start"] for e in entries]
            if not all(header_end <= t < end for t in targets):
                return None
            if any(targets[i] >= targets[i + 1] for i in range(len(targets) - 1)):
                return None
            for i, entry in enumerate(entries):
                entry["end"] = entries[i + 1]["start"] if i + 1 < len(entries) else end
            return {
                "header_end": header_end,
                "entries": entries,
            }

        if p + 2 >= end:
            return None
        ptr16 = rom[p + 1] | (rom[p + 2] << 8)
        target = (start & ~0xFFFF) | ptr16
        if target < start:
            target += 0x10000
        entries.append(
            {
                "entry_id": entry_id,
                "header_field": p,
                "start": target,
            }
        )
        p += 3

    return None


def tileset_pointer(rom: bytes, tileset_id: int) -> int:
    off = file_from_cpu(0xCE, 0x2000 + (tileset_id - 1) * 2)
    return u16_file(rom, off)


def layout_pointer(rom: bytes, layout_id: int) -> int:
    off = file_from_cpu(0xCF, 0x2000) + (layout_id - 1) * 3
    return u24_file(rom, off)


def layout_meta(rom: bytes, layout_id: int) -> dict:
    ptr = layout_pointer(rom, layout_id)
    bank = (ptr >> 16) & 0xFF
    addr = ptr & 0xFFFF
    off = file_from_cpu(bank, addr)
    flags = rom[off]
    width = rom[off + 1]
    height = rom[off + 2]
    cell_count = rom[off + 3] | (rom[off + 4] << 8)
    return {
        "layout_ptr": f"{bank:02X}:{addr:04X}",
        "layout_flags": f"0x{flags:02X}",
        "layout_width_chunks": width,
        "layout_height_chunks": height,
        "layout_cell_count": cell_count,
        "logical_width_metatiles": width * 16,
        "logical_height_metatiles": height * 16,
    }


def build_corpus(rom: bytes) -> tuple[list[dict], dict]:
    packs = []
    rejected = []
    for pack_id in range(FIRST_REAL_PACK, LAST_REAL_PACK + 1):
        parsed = parse_same_bank_pack(rom, pack_id)
        if parsed is None:
            rejected.append(pack_id)
        else:
            packs.append(parsed)

    records = []
    for pack in packs:
        records.extend(pack["records"])

    # This one is independently identified as a pointer/table blob.
    records = [
        r for r in records
        if (r["pack_id"], r["record_index"]) not in EXCLUDED_NON_VM_RECORDS
    ]

    valid_header_count = 0
    substream_count = 0
    for record in records:
        header = parse_record_header(rom, record)
        record["header"] = header
        if header:
            valid_header_count += 1
            substream_count += len(header["entries"])

    summary = {
        "same_bank_pack_count": len(packs),
        "cross_or_nonconforming_pack_ids": [f"0x{x:02X}" for x in rejected],
        "known_cross_bank_pack_ids": [f"0x{x:02X}" for x in sorted(KNOWN_CROSS_BANK_PACKS)],
        "bounded_vm_record_count": len(records),
        "excluded_non_vm_records": [
            {"pack_id": f"0x{p:02X}", "record_index": r}
            for p, r in sorted(EXCLUDED_NON_VM_RECORDS)
        ],
        "records_with_valid_entry_header": valid_header_count,
        "valid_substream_entries": substream_count,
    }
    return records, summary


def candidate_rows(rom: bytes, records: list[dict]) -> tuple[list[dict], list[dict]]:
    primary = []
    all_secondary_shape = []

    for record in records:
        header = record["header"]
        if not header:
            continue

        pack_id = record["pack_id"]
        record_index = record["record_index"]
        record_start = record["start"]
        record_end = record["end"]

        for entry in header["entries"]:
            entry_id = entry["entry_id"]
            stream_start = entry["start"]
            stream_end = entry["end"]

            # Primary normal-map-shaped 0x50.
            for p in range(stream_start, max(stream_start, stream_end - 3)):
                if rom[p] != 0x50 or p + 4 > stream_end:
                    continue
                tileset_id = rom[p + 1]
                layout_id = rom[p + 2]
                variant = rom[p + 3]
                if not (1 <= tileset_id <= 60):
                    continue
                if not (1 <= layout_id <= 203):
                    continue
                # C0:C6FD is 1-based and wrappers feed 1/2/3.
                if not (1 <= variant <= 3):
                    continue

                confirmed_signature = (
                    p >= stream_start + len(CONFIRMED_SETUP_SIGNATURE)
                    and rom[p - len(CONFIRMED_SETUP_SIGNATURE) : p]
                    == CONFIRMED_SETUP_SIGNATURE
                )
                evidence = (
                    "confirmed_setup_signature"
                    if confirmed_signature
                    else "strong_structural_candidate_mode_gate_unresolved"
                )

                tptr = tileset_pointer(rom, tileset_id)
                meta = layout_meta(rom, layout_id)

                row = {
                    "pack_id_dec": pack_id,
                    "pack_id_hex": f"0x{pack_id:02X}",
                    "record_index": record_index,
                    "record_start": cpu_from_file(record_start),
                    "record_end_exclusive": cpu_from_file(record_end),
                    "entry_id_dec": entry_id,
                    "entry_id_hex": f"0x{entry_id:02X}",
                    "substream_start": cpu_from_file(stream_start),
                    "substream_end_exclusive": cpu_from_file(stream_end),
                    "command_addr": cpu_from_file(p),
                    "opcode": "0x50",
                    "primary_tileset_id": tileset_id,
                    "primary_tileset_ptr": f"CE:{tptr:04X}",
                    "primary_layout_id": layout_id,
                    "map_variant": variant,
                    "evidence_class": evidence,
                    "confirmed_setup_signature": confirmed_signature,
                    **meta,
                    "immediate_secondary": False,
                    "secondary_command_addr": "",
                    "secondary_tileset_id": "",
                    "secondary_tileset_ptr": "",
                    "secondary_layout_id": "",
                    "secondary_layout_ptr": "",
                }

                # Immediate 0x51 is structurally compelling because normal 0x50
                # consumes exactly four bytes.
                if p + 7 <= stream_end and rom[p + 4] == 0x51:
                    st = rom[p + 5]
                    sl = rom[p + 6]
                    if 1 <= st <= 60 and 1 <= sl <= 203:
                        sptr = tileset_pointer(rom, st)
                        lptr = layout_pointer(rom, sl)
                        row.update(
                            {
                                "immediate_secondary": True,
                                "secondary_command_addr": cpu_from_file(p + 4),
                                "secondary_tileset_id": st,
                                "secondary_tileset_ptr": f"CE:{sptr:04X}",
                                "secondary_layout_id": sl,
                                "secondary_layout_ptr": f"{(lptr >> 16) & 0xFF:02X}:{lptr & 0xFFFF:04X}",
                            }
                        )
                primary.append(row)

            # Keep range-plausible standalone 0x51 rows separately. These are
            # mode-ambiguous because $1398 can route the same opcode to bank82.
            for p in range(stream_start, max(stream_start, stream_end - 2)):
                if rom[p] != 0x51 or p + 3 > stream_end:
                    continue
                st = rom[p + 1]
                sl = rom[p + 2]
                if not (1 <= st <= 60 and 1 <= sl <= 203):
                    continue
                sptr = tileset_pointer(rom, st)
                lptr = layout_pointer(rom, sl)
                all_secondary_shape.append(
                    {
                        "pack_id_dec": pack_id,
                        "pack_id_hex": f"0x{pack_id:02X}",
                        "record_index": record_index,
                        "record_start": cpu_from_file(record_start),
                        "record_end_exclusive": cpu_from_file(record_end),
                        "entry_id_dec": entry_id,
                        "entry_id_hex": f"0x{entry_id:02X}",
                        "substream_start": cpu_from_file(stream_start),
                        "substream_end_exclusive": cpu_from_file(stream_end),
                        "command_addr": cpu_from_file(p),
                        "opcode": "0x51",
                        "secondary_tileset_id": st,
                        "secondary_tileset_ptr": f"CE:{sptr:04X}",
                        "secondary_layout_id": sl,
                        "secondary_layout_ptr": f"{(lptr >> 16) & 0xFF:02X}:{lptr & 0xFFFF:04X}",
                        "evidence_class": "mode_ambiguous_secondary_shape",
                    }
                )

    primary_by_addr = {r["command_addr"]: r for r in primary}
    paired_secondary_addrs = {
        r["secondary_command_addr"]
        for r in primary
        if r["immediate_secondary"]
    }
    for row in all_secondary_shape:
        if row["command_addr"] in paired_secondary_addrs:
            row["evidence_class"] = "strong_immediate_secondary_pair"

    return primary, all_secondary_shape


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("data/maps/selectors"))
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM SHA-256: {sha}")

    records, corpus = build_corpus(rom)
    primary, secondary = candidate_rows(rom, records)

    confirmed = [r for r in primary if r["confirmed_setup_signature"]]
    structural = [r for r in primary if not r["confirmed_setup_signature"]]
    paired = [r for r in primary if r["immediate_secondary"]]
    secondary_paired = [r for r in secondary if r["evidence_class"] == "strong_immediate_secondary_pair"]
    secondary_ambiguous = [r for r in secondary if r["evidence_class"] != "strong_immediate_secondary_pair"]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "primary_map_selector_catalog.csv", primary)
    write_csv(args.out_dir / "secondary_map_selector_candidates.csv", secondary)

    summary = {
        "schema_version": 1,
        "kind": "derived_map_selector_catalog",
        "rom_sha256": sha,
        "policy": "Addresses/IDs/derived metadata only; no ROM payloads.",
        "normal_vs_special_dispatch_caveat": (
            "For opcode >= 0x50, C4:87A2 routes to bank82 special dispatch when "
            "$1398 != 0. Only the 65 setup-signature rows are already promoted "
            "as confirmed normal-map selectors; remaining primary rows are "
            "strong structural candidates until the mode gate is resolved."
        ),
        "corpus": corpus,
        "primary": {
            "strong_shape_total": len(primary),
            "confirmed_setup_signature": len(confirmed),
            "additional_structural_candidates": len(structural),
            "unique_configurations": len(
                {
                    (
                        r["primary_tileset_id"],
                        r["primary_layout_id"],
                        r["map_variant"],
                    )
                    for r in primary
                }
            ),
            "distinct_tileset_ids": len({r["primary_tileset_id"] for r in primary}),
            "distinct_layout_ids": len({r["primary_layout_id"] for r in primary}),
            "variant_counts": {
                str(k): v
                for k, v in sorted(Counter(r["map_variant"] for r in primary).items())
            },
            "families_with_candidates": len({r["pack_id_dec"] for r in primary}),
            "immediate_secondary_pair_rows": len(paired),
        },
        "secondary": {
            "range_plausible_substream_rows": len(secondary),
            "strong_immediate_pairs": len(secondary_paired),
            "mode_ambiguous_standalone_rows": len(secondary_ambiguous),
            "unique_immediate_pair_configurations": len(
                {
                    (
                        r["primary_tileset_id"],
                        r["primary_layout_id"],
                        r["map_variant"],
                        r["secondary_tileset_id"],
                        r["secondary_layout_id"],
                    )
                    for r in paired
                }
            ),
        },
        "stable_interior": {
            "expected_primary_command": "50 07 0F 02",
            "confirmed_addresses": ["CB:DE70", "CC:5391", "CE:0F2B"],
            "catalog_matches": [
                r["command_addr"]
                for r in primary
                if r["primary_tileset_id"] == 7
                and r["primary_layout_id"] == 15
                and r["map_variant"] == 2
            ],
        },
        "outputs": [
            "primary_map_selector_catalog.csv",
            "secondary_map_selector_candidates.csv",
            "primary_map_selector_summary.json",
        ],
    }

    (args.out_dir / "primary_map_selector_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
