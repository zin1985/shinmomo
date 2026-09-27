#!/usr/bin/env python3
"""Decode Shinmomo CF map-layout records and optionally validate runtime evidence.

The tool reconstructs logical metatile IDs from the ROM-side CF:2000 layout
catalog. Full decoded grids are not written unless --grid-csv is explicitly
requested. The normal --output JSON contains derived metadata, hashes and
validation counts only.

Confirmed stream selector implementations are based on C0:D145/D14E dispatch:
  0 -> C0:C057 / C0:C0C8 : value + run-count
  1 -> C0:C067 / C0:C0F2 : binary run-count
  2 -> C0:C02A / C0:C077 : flag/reuse stream
  3 -> C0:BCEE / C0:BD28 : 256-byte-ring literal/back-reference stream
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def hirom_offset(bank: int, addr: int) -> int:
    return ((bank & 0x3F) << 16) | (addr & 0xFFFF)


def u16_at(rom: bytes, bank: int, addr: int) -> int:
    o = hirom_offset(bank, addr)
    return rom[o] | (rom[o + 1] << 8)


def u24_off(rom: bytes, off: int) -> int:
    return rom[off] | (rom[off + 1] << 8) | (rom[off + 2] << 16)


def cpu_addr(value: int) -> str:
    return f"{(value >> 16) & 0xFF:02X}:{value & 0xFFFF:04X}"


class Reader:
    def __init__(self, rom: bytes, ptr: int):
        self.rom = rom
        self.ptr = ptr & 0xFFFFFF

    def read(self) -> int:
        bank = (self.ptr >> 16) & 0xFF
        addr = self.ptr & 0xFFFF
        value = self.rom[hirom_offset(bank, addr)]
        self.ptr = (self.ptr + 1) & 0xFFFFFF
        return value


def decode_selector_0(rom: bytes, ptr: int, count: int = 256) -> bytes:
    """C057/C0C8: literal value followed by (run_length - 1)."""
    r = Reader(rom, ptr)
    out = bytearray()
    while len(out) < count:
        value = r.read()
        run = r.read() + 1
        out.extend([value] * min(run, count - len(out)))
    return bytes(out)


def decode_selector_1(rom: bytes, ptr: int, count: int = 256) -> bytes:
    """C067/C0F2: high bit is 0/1 value, low 7 bits encode run_length - 1."""
    r = Reader(rom, ptr)
    out = bytearray()
    while len(out) < count:
        token = r.read()
        value = 1 if token & 0x80 else 0
        run = (token & 0x7F) + 1
        out.extend([value] * min(run, count - len(out)))
    return bytes(out)


def decode_selector_2(rom: bytes, ptr: int, count: int = 256) -> bytes:
    """C02A/C077: one flag bit per output; 1=new byte, 0=reuse previous."""
    r = Reader(rom, ptr)
    out = bytearray()
    previous = 0
    flags = r.read()
    mask = 0x80
    while len(out) < count:
        if flags & mask:
            previous = r.read()
        out.append(previous)
        mask >>= 1
        if mask == 0:
            flags = r.read()
            mask = 0x80
    return bytes(out)


def decode_selector_3(rom: bytes, ptr: int, count: int = 256) -> bytes:
    """BCEE/BD28: MSB-first flags plus a 256-byte history ring.

    Flag 1 emits a literal. Flag 0 emits a back-reference. Match lengths are
    packed two per length byte: high nibble for the first match, low nibble for
    the second. The machine counter plus the immediate first copy gives
    nibble + 2 output bytes.
    """
    r = Reader(rom, ptr)
    history = bytearray(256)
    write_pos = 0xEF
    out = bytearray()

    flags = 0
    bits_left = 0
    match_pos = 0
    match_remaining = 0
    saved_length_byte = 0
    match_pair_phase = 0

    while len(out) < count:
        if match_remaining:
            value = history[match_pos]
            match_pos = (match_pos + 1) & 0xFF
            history[write_pos] = value
            write_pos = (write_pos + 1) & 0xFF
            out.append(value)
            match_remaining -= 1
            continue

        if bits_left == 0:
            flags = r.read()
            bits_left = 8

        literal = bool(flags & 0x80)
        flags = (flags << 1) & 0xFF
        bits_left -= 1
        token = r.read()

        if literal:
            history[write_pos] = token
            write_pos = (write_pos + 1) & 0xFF
            out.append(token)
            continue

        match_pos = token
        if match_pair_phase == 0:
            saved_length_byte = r.read()
            machine_count = (saved_length_byte >> 4) + 1
            match_pair_phase = 1
        else:
            machine_count = (saved_length_byte & 0x0F) + 1
            match_pair_phase = 0

        value = history[match_pos]
        match_pos = (match_pos + 1) & 0xFF
        history[write_pos] = value
        write_pos = (write_pos + 1) & 0xFF
        out.append(value)
        match_remaining = machine_count

    return bytes(out)


DECODERS = {
    0: ("value_run", decode_selector_0),
    1: ("binary_run", decode_selector_1),
    2: ("flag_reuse", decode_selector_2),
    3: ("ring_backref", decode_selector_3),
}


def layout_pointer(rom: bytes, layout_id: int) -> int:
    if layout_id < 1:
        raise ValueError("layout_id must be >= 1")
    table = hirom_offset(0xCF, 0x2000)
    return u24_off(rom, table + (layout_id - 1) * 3)


def tileset_pointer(rom: bytes, tileset_id: int) -> int:
    if tileset_id < 1:
        raise ValueError("tileset_id must be >= 1")
    return u16_at(rom, 0xCE, 0x2000 + (tileset_id - 1) * 2)


def tileset_next_pointer(rom: bytes, tileset_id: int) -> int | None:
    value = u16_at(rom, 0xCE, 0x2000 + tileset_id * 2)
    return None if value == 0xFFFF else value


def parse_layout(rom: bytes, layout_id: int) -> dict:
    ptr = layout_pointer(rom, layout_id)
    bank = (ptr >> 16) & 0xFF
    addr = ptr & 0xFFFF
    if bank != 0xCF:
        raise ValueError(f"layout {layout_id} leaves bank CF: {cpu_addr(ptr)}")

    o = hirom_offset(bank, addr)
    flags = rom[o]
    width = rom[o + 1]
    height = rom[o + 2]
    cell_count = rom[o + 3] | (rom[o + 4] << 8)
    if cell_count != width * height:
        raise ValueError(
            f"layout {layout_id} cell count mismatch: {cell_count} != {width}*{height}"
        )

    wide_ids = bool(flags & 0xF0)
    streams_per_cell = 2 if wide_ids else 1
    spacing = cell_count * streams_per_cell

    cells = []
    decoded_pages = []
    for cell in range(cell_count):
        descriptors = []
        pages = []
        for plane in range(streams_per_cell):
            base = o + 5 + cell * streams_per_cell + plane
            b0 = rom[base]
            b1 = rom[base + spacing]
            b2 = rom[base + 2 * spacing]
            selector = (b2 >> 6) & 0x03
            source_ptr = ((b2 | 0xC0) << 16) | (b1 << 8) | b0
            decoder_name, decoder = DECODERS[selector]
            data = decoder(rom, source_ptr, 256)
            pages.append(data)
            decoded_pages.append(
                {
                    "cell": cell,
                    "plane": plane,
                    "selector": selector,
                    "decoder": decoder_name,
                    "source_ptr": cpu_addr(source_ptr),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "data": data,
                }
            )
            descriptors.append(
                {
                    "plane": plane,
                    "selector": selector,
                    "decoder": decoder_name,
                    "source_ptr": cpu_addr(source_ptr),
                }
            )

        ids = []
        for i in range(256):
            value = pages[0][i]
            if streams_per_cell == 2:
                value |= pages[1][i] << 8
            ids.append(value)
        cells.append({"cell": cell, "descriptors": descriptors, "ids": ids})

    grid_w = width * 16
    grid_h = height * 16
    grid = [[0] * grid_w for _ in range(grid_h)]
    for cell in cells:
        ci = cell["cell"]
        cx = ci % width
        cy = ci // width
        ids = cell["ids"]
        for y in range(16):
            for x in range(16):
                grid[cy * 16 + y][cx * 16 + x] = ids[y * 16 + x]

    return {
        "layout_id": layout_id,
        "record_ptr": cpu_addr(ptr),
        "flags": flags,
        "map_mode_low_nibble": flags & 0x0F,
        "wide_metatile_ids": wide_ids,
        "width_chunks": width,
        "height_chunks": height,
        "cell_count": cell_count,
        "streams_per_cell": streams_per_cell,
        "cells": cells,
        "decoded_pages": decoded_pages,
        "grid": grid,
    }


def expand_tileset(rom: bytes, grid: list[list[int]], tileset_id: int) -> dict:
    ptr = tileset_pointer(rom, tileset_id)
    next_ptr = tileset_next_pointer(rom, tileset_id)
    max_id = max(max(row) for row in grid)
    if next_ptr is not None and ptr + (max_id + 1) * 8 > next_ptr:
        raise ValueError(
            f"metatile id {max_id} exceeds tileset {tileset_id} block "
            f"{ptr:04X}..{next_ptr:04X}"
        )

    height = len(grid)
    width = len(grid[0])
    expanded = [[0] * (width * 2) for _ in range(height * 2)]

    for my, row in enumerate(grid):
        for mx, metatile_id in enumerate(row):
            base = ptr + metatile_id * 8
            values = [u16_at(rom, 0xCE, base + i * 2) for i in range(4)]
            expanded[my * 2][mx * 2] = values[0]
            expanded[my * 2][mx * 2 + 1] = values[1]
            expanded[my * 2 + 1][mx * 2] = values[2]
            expanded[my * 2 + 1][mx * 2 + 1] = values[3]

    return {
        "tileset_id": tileset_id,
        "block_ptr": f"CE:{ptr:04X}",
        "next_block_ptr": None if next_ptr is None else f"CE:{next_ptr:04X}",
        "expanded": expanded,
    }


def grid_u16_bytes(grid: list[list[int]]) -> bytes:
    return b"".join(
        int(value & 0xFFFF).to_bytes(2, "little")
        for row in grid
        for value in row
    )


def write_grid_csv(path: Path, grid: list[list[int]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["y", "x", "value_dec", "value_hex"])
        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                writer.writerow([y, x, value, f"0x{value:04X}"])


def validate_staging(layout: dict, capture_path: Path) -> dict:
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    runtime = bytes(capture["bytes"])
    expected = b"".join(page["data"] for page in layout["decoded_pages"])
    if len(runtime) < len(expected):
        raise ValueError(
            f"staging capture too short: {len(runtime)} < {len(expected)}"
        )

    pages = []
    for i, page in enumerate(layout["decoded_pages"]):
        actual = runtime[i * 256 : (i + 1) * 256]
        pages.append(
            {
                "cell": page["cell"],
                "plane": page["plane"],
                "selector": page["selector"],
                "source_ptr": page["source_ptr"],
                "expected_sha256": page["sha256"],
                "runtime_sha256": hashlib.sha256(actual).hexdigest(),
                "byte_differences": sum(a != b for a, b in zip(page["data"], actual)),
            }
        )

    return {
        "capture_id": capture.get("id"),
        "frame": capture.get("frame"),
        "start": capture.get("start"),
        "length": capture.get("length"),
        "compared_bytes": len(expected),
        "byte_differences": sum(a != b for a, b in zip(expected, runtime)),
        "exact_match": expected == runtime[: len(expected)],
        "pages": pages,
    }


def validate_vram(expanded: list[list[int]], vram_path: Path, bases: list[int]) -> dict:
    vram = vram_path.read_bytes()
    if len(expanded) != 32 or len(expanded[0]) != 64:
        return {
            "performed": False,
            "reason": "current comparator expects a 64x32 expanded tile-entry grid",
        }
    if len(bases) != 2:
        raise ValueError("64x32 comparator requires exactly two 0x800-byte VRAM page bases")

    halves = [
        [value for row in expanded for value in row[:32]],
        [value for row in expanded for value in row[32:64]],
    ]
    page_results = []
    all_mismatches = []

    for index, base in enumerate(bases):
        page = vram[base : base + 0x800]
        runtime_words = [
            page[i] | (page[i + 1] << 8) for i in range(0, len(page), 2)
        ]
        expected_words = halves[index]
        mismatches = [
            (i, expected, actual)
            for i, (expected, actual) in enumerate(zip(expected_words, runtime_words))
            if expected != actual
        ]
        all_mismatches.extend((index, *m) for m in mismatches)
        page_results.append(
            {
                "page_base": f"0x{base:04X}",
                "runtime_sha256": hashlib.sha256(page).hexdigest(),
                "expected_sha256": hashlib.sha256(
                    b"".join(v.to_bytes(2, "little") for v in expected_words)
                ).hexdigest(),
                "word_differences": len(mismatches),
                "exact_words": 1024 - len(mismatches),
                "all_mismatches_are_runtime_0x0100": all(
                    actual == 0x0100 for _, _, actual in mismatches
                ),
            }
        )

    return {
        "performed": True,
        "runtime_capture_label": vram_path.parent.name,
        "page_results": page_results,
        "total_words": 2048,
        "exact_words": 2048 - len(all_mismatches),
        "word_differences": len(all_mismatches),
        "all_mismatches_are_runtime_0x0100": all(
            actual == 0x0100 for _, _, _, actual in all_mismatches
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--layout-id", type=int, required=True)
    ap.add_argument("--tileset-id", type=int)
    ap.add_argument("--staging-json", type=Path)
    ap.add_argument("--vram", type=Path)
    ap.add_argument("--vram-pages", nargs=2, type=lambda s: int(s, 0), default=[0x1000, 0x1800])
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--grid-csv", type=Path)
    ap.add_argument("--expanded-grid-csv", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    layout = parse_layout(rom, args.layout_id)
    grid = layout["grid"]
    flat_ids = [value for row in grid for value in row]
    grid_bytes = grid_u16_bytes(grid)

    summary = {
        "schema_version": 1,
        "kind": "derived_map_layout_decode",
        "policy": "Metadata/hashes by default; full decoded grids are opt-in outputs.",
        "rom_sha256": hashlib.sha256(rom).hexdigest().upper(),
        "layout": {
            "layout_id": layout["layout_id"],
            "record_ptr": layout["record_ptr"],
            "flags_hex": f"0x{layout['flags']:02X}",
            "map_mode_low_nibble": layout["map_mode_low_nibble"],
            "wide_metatile_ids": layout["wide_metatile_ids"],
            "width_chunks": layout["width_chunks"],
            "height_chunks": layout["height_chunks"],
            "cell_count": layout["cell_count"],
            "streams_per_cell": layout["streams_per_cell"],
            "logical_width_metatiles": len(grid[0]),
            "logical_height_metatiles": len(grid),
            "unique_metatile_ids": len(set(flat_ids)),
            "min_metatile_id": min(flat_ids),
            "max_metatile_id": max(flat_ids),
            "logical_grid_sha256_u16le": hashlib.sha256(grid_bytes).hexdigest(),
            "descriptors": [
                {
                    "cell": page["cell"],
                    "plane": page["plane"],
                    "selector": page["selector"],
                    "decoder": page["decoder"],
                    "source_ptr": page["source_ptr"],
                    "decoded_page_sha256": page["sha256"],
                }
                for page in layout["decoded_pages"]
            ],
        },
    }

    if args.staging_json:
        summary["staging_validation"] = validate_staging(layout, args.staging_json)

    if args.tileset_id:
        tileset = expand_tileset(rom, grid, args.tileset_id)
        expanded = tileset["expanded"]
        expanded_bytes = grid_u16_bytes(expanded)
        summary["tileset"] = {
            "tileset_id": tileset["tileset_id"],
            "block_ptr": tileset["block_ptr"],
            "next_block_ptr": tileset["next_block_ptr"],
            "expanded_width_tiles": len(expanded[0]),
            "expanded_height_tiles": len(expanded),
            "expanded_grid_sha256_u16le": hashlib.sha256(expanded_bytes).hexdigest(),
        }
        if len(expanded) == 32 and len(expanded[0]) == 64:
            left = [[*row[:32]] for row in expanded]
            right = [[*row[32:64]] for row in expanded]
            summary["tileset"]["left_screen_sha256_u16le"] = hashlib.sha256(
                grid_u16_bytes(left)
            ).hexdigest()
            summary["tileset"]["right_screen_sha256_u16le"] = hashlib.sha256(
                grid_u16_bytes(right)
            ).hexdigest()

        if args.vram:
            summary["vram_validation"] = validate_vram(
                expanded, args.vram, args.vram_pages
            )
        if args.expanded_grid_csv:
            args.expanded_grid_csv.parent.mkdir(parents=True, exist_ok=True)
            write_grid_csv(args.expanded_grid_csv, expanded)

    if args.grid_csv:
        args.grid_csv.parent.mkdir(parents=True, exist_ok=True)
        write_grid_csv(args.grid_csv, grid)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
