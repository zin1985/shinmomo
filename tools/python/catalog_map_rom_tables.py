#!/usr/bin/env python3
"""Catalog Shin Momotarou Densetsu ROM-side map tables without exporting payload bytes.

This tool emits only derived pointer/header metadata:
- CE:2000 word-pointer table for metatile/tileset definition blocks;
- CF:0000 parallel word-pointer table used by the map system;
- CF:2000 packed 24-bit pointer table for map-layout records;
- layout record header metadata and inferred record lengths.

Raw ROM bytes and map payloads are intentionally not written to the output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


def hirom_offset(bank: int, addr: int) -> int:
    if not (0xC0 <= bank <= 0xFF and 0 <= addr <= 0xFFFF):
        raise ValueError(f"unsupported HiROM CPU address {bank:02X}:{addr:04X}")
    return ((bank & 0x3F) << 16) | addr


def u16(rom: bytes, bank: int, addr: int) -> int:
    o = hirom_offset(bank, addr)
    return rom[o] | (rom[o + 1] << 8)


def u24_at_offset(rom: bytes, offset: int) -> int:
    return rom[offset] | (rom[offset + 1] << 8) | (rom[offset + 2] << 16)


def cpu_addr(value: int) -> str:
    return f"{(value >> 16) & 0xFF:02X}:{value & 0xFFFF:04X}"


def parse_word_table(rom: bytes, bank: int, addr: int, max_entries: int = 256) -> list[int]:
    out: list[int] = []
    for i in range(max_entries):
        value = u16(rom, bank, addr + i * 2)
        if value == 0xFFFF:
            break
        out.append(value)
    if not out:
        raise ValueError(f"empty word pointer table at {bank:02X}:{addr:04X}")
    return out


def parse_layout_table(rom: bytes) -> tuple[list[dict], dict]:
    table_bank = 0xCF
    table_addr = 0x2000
    table_off = hirom_offset(table_bank, table_addr)
    first_ptr = u24_at_offset(rom, table_off)
    first_bank = (first_ptr >> 16) & 0xFF
    first_addr = first_ptr & 0xFFFF

    if first_bank != table_bank:
        raise ValueError(f"CF:2000 first layout pointer leaves bank CF: {cpu_addr(first_ptr)}")
    table_bytes = first_addr - table_addr
    if table_bytes <= 0 or table_bytes % 3:
        raise ValueError(
            f"CF:2000 table length is not a positive multiple of 3: 0x{table_bytes:X}"
        )
    pointer_count = table_bytes // 3

    ptrs = [u24_at_offset(rom, table_off + i * 3) for i in range(pointer_count)]
    for i, ptr in enumerate(ptrs):
        if ((ptr >> 16) & 0xFF) != 0xCF:
            raise ValueError(f"layout pointer {i + 1} leaves bank CF: {cpu_addr(ptr)}")
        if i and ptr <= ptrs[i - 1]:
            raise ValueError(
                f"layout pointers are not strictly increasing at {i + 1}: "
                f"{cpu_addr(ptrs[i - 1])} -> {cpu_addr(ptr)}"
            )

    rows: list[dict] = []
    mismatches: list[int] = []
    modes: Counter[int] = Counter()

    for i, ptr in enumerate(ptrs):
        bank = (ptr >> 16) & 0xFF
        addr = ptr & 0xFFFF
        o = hirom_offset(bank, addr)
        mode = rom[o]
        width = rom[o + 1]
        height = rom[o + 2]
        cell_count = rom[o + 3] | (rom[o + 4] << 8)

        stride = 6 if mode == 0x80 else 3 if mode in (0x00, 0x01) else None
        expected_len = None if stride is None else 5 + cell_count * stride
        next_ptr = ptrs[i + 1] if i + 1 < len(ptrs) else None
        actual_len = None if next_ptr is None else next_ptr - ptr
        dims_match = cell_count == width * height
        length_match = (
            None
            if actual_len is None or expected_len is None
            else actual_len == expected_len
        )
        if not dims_match or (length_match is False):
            mismatches.append(i + 1)
        modes[mode] += 1

        rows.append(
            {
                "layout_id": i + 1,
                "record_ptr": cpu_addr(ptr),
                "mode_hex": f"0x{mode:02X}",
                "width": width,
                "height": height,
                "cell_count": cell_count,
                "cell_count_matches_width_x_height": dims_match,
                "payload_stride_bytes": stride,
                "expected_record_len": expected_len,
                "actual_record_len_to_next_ptr": actual_len,
                "record_len_matches": length_match,
                "expected_record_end": (
                    None if expected_len is None else cpu_addr(ptr + expected_len)
                ),
            }
        )

    summary = {
        "table": "CF:2000",
        "first_record": cpu_addr(first_ptr),
        "table_bytes": table_bytes,
        "pointer_count": pointer_count,
        "mode_counts": {f"0x{k:02X}": v for k, v in sorted(modes.items())},
        "all_dimension_counts_match": all(
            r["cell_count_matches_width_x_height"] for r in rows
        ),
        "all_nonfinal_record_lengths_match": all(
            r["record_len_matches"] is not False for r in rows
        ),
        "mismatch_layout_ids": mismatches,
    }
    return rows, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) < 0x100000:
        raise SystemExit(f"ROM is unexpectedly small: {len(rom)} bytes")

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    ce = parse_word_table(rom, 0xCE, 0x2000)
    cf_aux = parse_word_table(rom, 0xCF, 0x0000)
    layouts, layout_summary = parse_layout_table(rom)

    tileset_rows: list[dict] = []
    for i, ptr16 in enumerate(ce):
        next_ptr = ce[i + 1] if i + 1 < len(ce) else None
        aux = cf_aux[i] if i < len(cf_aux) else None
        tileset_rows.append(
            {
                "tileset_id": i + 1,
                "metatile_block_ptr": f"CE:{ptr16:04X}",
                "next_metatile_block_ptr": (
                    None if next_ptr is None else f"CE:{next_ptr:04X}"
                ),
                "span_to_next_bytes": None if next_ptr is None else next_ptr - ptr16,
                "parallel_cf0000_ptr": None if aux is None else f"CF:{aux:04X}",
            }
        )

    write_csv(out / "tileset_pointer_catalog.csv", tileset_rows)
    write_csv(out / "layout_record_catalog.csv", layouts)

    summary = {
        "schema_version": 1,
        "kind": "derived_rom_map_table_catalog",
        "policy": (
            "Pointer/header metadata only. Raw ROM bytes and record payloads are "
            "not exported."
        ),
        "rom_size": len(rom),
        "rom_sha256": hashlib.sha256(rom).hexdigest().upper(),
        "tileset_table": {
            "address": "CE:2000",
            "entry_width_bytes": 2,
            "non_ffff_entries": len(ce),
            "first_target": f"CE:{ce[0]:04X}",
            "last_target": f"CE:{ce[-1]:04X}",
            "parallel_cf0000_non_ffff_entries": len(cf_aux),
            "parallel_cf0000_first_target": f"CF:{cf_aux[0]:04X}",
            "parallel_cf0000_last_target": f"CF:{cf_aux[-1]:04X}",
        },
        "layout_table": layout_summary,
        "inferred_layout_record_schema": {
            "header_bytes": 5,
            "byte0": "mode/flags",
            "byte1": "width",
            "byte2": "height",
            "bytes3_4_le": "cell_count (= width * height in all catalogued records)",
            "mode_0x00_payload_stride_bytes_per_cell": 3,
            "mode_0x01_payload_stride_bytes_per_cell": 3,
            "mode_0x80_payload_stride_bytes_per_cell": 6,
        },
        "outputs": [
            "tileset_pointer_catalog.csv",
            "layout_record_catalog.csv",
            "map_rom_table_summary.json",
        ],
    }
    (out / "map_rom_table_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
