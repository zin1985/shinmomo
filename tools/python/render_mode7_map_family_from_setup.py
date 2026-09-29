#!/usr/bin/env python3
"""Render Mode-7 map families from ROM setup resources only.

The graphics resource comes from normal-VM opcode 0x10.
The low/mid CGRAM range comes from normal-VM opcode 0x11.
The high CGRAM half (0x80..0xFF) is reconstructed from a ROM-resident
common profile that is byte-for-byte validated against the tileset-1
runtime CGRAM capture.

Mode-7 pixel index 0 is exported with alpha 0.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

import decode_map_layout as mapdec
import render_normal_map_family_from_setup as normal


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"

# target_start, target_end_exclusive, ROM file offset, CPU label
COMMON_HIGH_SEGMENTS = [
    (0x80, 0xA0, 0x004A8D, "C0:4A8D"),
    (0xA0, 0xB0, 0x001DBF, "C0:1DBF"),
    (0xB0, 0xC8, 0x0026D9, "C0:26D9"),
    (0xC8, 0x100, 0x0AC4EB, "CA:C4EB"),
]
COMMON_HIGH_SHA256 = "87F72E94BCC2A789E67E2EA53381B00B1A53D93C0B09F64149E2A8D8C4784966"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rgb555(word: int) -> tuple[int, int, int]:
    return (
        round((word & 0x1F) * 255 / 31),
        round(((word >> 5) & 0x1F) * 255 / 31),
        round(((word >> 10) & 0x1F) * 255 / 31),
    )


def config_layout_ids(path: Path, tileset_id: int) -> list[int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return sorted({
        int(row["primary_layout_id"])
        for row in rows
        if int(row["primary_tileset_id"]) == tileset_id
    })


def common_high_palette(rom: bytes):
    raw = bytearray(0x100)
    entries = {}
    sources = []
    for first, last, file_off, cpu_label in COMMON_HIGH_SEGMENTS:
        length = (last - first) * 2
        payload = rom[file_off:file_off + length]
        if len(payload) != length:
            raise ValueError(f"truncated common high palette at {cpu_label}")
        raw[(first - 0x80) * 2:(last - 0x80) * 2] = payload
        sources.append({
            "destination_first": first,
            "destination_last": last - 1,
            "rom_addr": cpu_label,
            "byte_count": length,
            "sha256": hashlib.sha256(payload).hexdigest().upper(),
        })
        for index in range(first, last):
            pos = (index - first) * 2
            word = payload[pos] | (payload[pos + 1] << 8)
            entries[index] = {
                "index": index,
                "bgr555": f"0x{word:04X}",
                "rgb888": list(rgb555(word)),
                "source": "common_high_profile",
                "source_addr": cpu_label,
            }
    digest = hashlib.sha256(raw).hexdigest().upper()
    if digest != COMMON_HIGH_SHA256:
        raise ValueError(
            f"common high palette SHA mismatch: {digest} != {COMMON_HIGH_SHA256}"
        )
    return bytes(raw), entries, sources


def build_palette(rom: bytes, palette_operand: int, descriptor_index: int):
    palette = [(0, 0, 0)] * 256
    covered = set()
    source_by_index = {}

    _, high_entries, high_sources = common_high_palette(rom)
    for index, entry in high_entries.items():
        palette[index] = tuple(entry["rgb888"])
        covered.add(index)
        source_by_index[index] = entry

    _, low_meta = normal.palette_from_opcode11(
        rom, palette_operand, descriptor_index
    )
    for entry in low_meta["entries"]:
        index = entry["index"]
        palette[index] = tuple(entry["rgb888"])
        covered.add(index)
        source_by_index[index] = {
            **entry,
            "source": "opcode11",
            "source_addr": low_meta["payload_addr"],
        }

    return palette, covered, source_by_index, low_meta, high_sources


def validate_mode7(
    graphics: bytes,
    palette_covered: set[int],
    rom: bytes,
    tileset_id: int,
    layout_ids: list[int],
):
    ptr = mapdec.tileset_pointer(rom, tileset_id)
    max_tile = -1
    used_tiles = set()
    used_colors = set()
    per_layout = {}

    for layout_id in layout_ids:
        layout = mapdec.parse_layout(rom, layout_id)
        if layout["map_mode_low_nibble"] != 1:
            raise ValueError(
                f"layout {layout_id} has mode "
                f"{layout['map_mode_low_nibble']}, expected 1"
            )
        mids = {mid for row in layout["grid"] for mid in row}
        tile_ids = set()
        for mid in mids:
            off = 0xE0000 + ptr + mid * 4
            raw = rom[off:off + 4]
            if len(raw) != 4:
                raise ValueError(f"layout {layout_id} CE definition truncated")
            tile_ids.update(raw)
        if tile_ids:
            max_tile = max(max_tile, max(tile_ids))
            used_tiles.update(tile_ids)
            for tile_id in tile_ids:
                start = tile_id * 64
                end = start + 64
                if end > len(graphics):
                    raise ValueError(
                        f"layout {layout_id} references tile {tile_id:#x} "
                        f"outside graphics resource ({len(graphics)} bytes)"
                    )
                used_colors.update(graphics[start:end])
        per_layout[layout_id] = {
            "metatile_ids": len(mids),
            "tile_ids": len(tile_ids),
            "max_tile_id": max(tile_ids) if tile_ids else None,
        }

    missing = sorted(
        index for index in used_colors
        if index != 0 and index not in palette_covered
    )
    if missing:
        raise ValueError(
            "Mode-7 graphics reference uncovered CGRAM indices: "
            + ",".join(f"{x:#x}" for x in missing)
        )
    return {
        "used_tile_count": len(used_tiles),
        "max_tile_id": max_tile,
        "used_color_indices": sorted(used_colors),
        "transparent_color_index": 0,
        "per_layout": per_layout,
    }


def render_layout(
    rom: bytes,
    graphics: bytes,
    palette: list[tuple[int, int, int]],
    tileset_id: int,
    layout_id: int,
) -> Image.Image:
    layout = mapdec.parse_layout(rom, layout_id)
    if layout["map_mode_low_nibble"] != 1:
        raise ValueError(f"layout {layout_id} is not Mode-7")

    ptr = mapdec.tileset_pointer(rom, tileset_id)
    width = len(layout["grid"][0]) * 16
    height = len(layout["grid"]) * 16
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    out = image.load()

    for my, row in enumerate(layout["grid"]):
        for mx, metatile_id in enumerate(row):
            base = 0xE0000 + ptr + metatile_id * 4
            tile_ids = rom[base:base + 4]
            if len(tile_ids) != 4:
                raise ValueError("Mode-7 CE definition truncated")
            for quadrant, tile_id in enumerate(tile_ids):
                source = tile_id * 64
                ox = mx * 16 + (quadrant & 1) * 8
                oy = my * 16 + (quadrant >> 1) * 8
                for y in range(8):
                    for x in range(8):
                        color_index = graphics[source + y * 8 + x]
                        if color_index == 0:
                            continue
                        out[ox + x, oy + y] = (*palette[color_index], 255)
    return image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--tileset-id", type=int, required=True)
    ap.add_argument("--gfx-operand", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--palette-operand", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--state0-descriptor-index", type=int, default=2)
    ap.add_argument("--layout-id", type=int, action="append")
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    graphics_meta = normal.graphics_descriptor(
        rom, args.gfx_operand, args.state0_descriptor_index
    )
    graphics = normal.decode_graphics_resource(
        rom, graphics_meta, args.gfx_operand
    )
    palette, covered, source_by_index, low_meta, high_sources = build_palette(
        rom, args.palette_operand, args.state0_descriptor_index
    )

    layout_ids = args.layout_id or config_layout_ids(
        args.config_index, args.tileset_id
    )
    validation = validate_mode7(
        graphics, covered, rom, args.tileset_id, layout_ids
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    maps = []
    for layout_id in layout_ids:
        image = render_layout(
            rom, graphics, palette, args.tileset_id, layout_id
        )
        png = args.out_dir / f"map_{layout_id:03d}.png"
        image.save(png, optimize=True)
        meta = {
            "schema_version": 1,
            "tileset_id": args.tileset_id,
            "layout_id": layout_id,
            "render_mode": "snes_mode7_rom_setup",
            "image_mode": "RGBA",
            "transparent_color_index": 0,
            "image_width_px": image.width,
            "image_height_px": image.height,
            "graphics_operand": args.gfx_operand,
            "palette_operand": args.palette_operand,
            "output_png": png.name,
            "output_png_sha256": sha256_file(png),
        }
        (args.out_dir / f"map_{layout_id:03d}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        maps.append(meta)
        print(f"rendered Mode-7 map {layout_id:03d}: {image.size}")

    palette_entries = []
    for index in range(256):
        rgb = palette[index]
        item = {
            "index": index,
            "rgb888": list(rgb),
            "covered": index in covered,
        }
        if index in source_by_index:
            item.update(source_by_index[index])
        palette_entries.append(item)

    resources = {
        "schema_version": 1,
        "kind": "mode7_rom_resources",
        "tileset_id": args.tileset_id,
        "graphics_operand": args.gfx_operand,
        "graphics_descriptor": graphics_meta,
        "graphics_decoded_sha256": hashlib.sha256(graphics).hexdigest().upper(),
        "palette_operand": args.palette_operand,
        "opcode11_palette": low_meta,
        "common_high_profile": {
            "destination_first": 0x80,
            "destination_last": 0xFF,
            "sha256": COMMON_HIGH_SHA256,
            "segments": high_sources,
            "validation": (
                "profile bytes are 256/256 byte-identical to the validated "
                "tileset-1 runtime CGRAM high half"
            ),
        },
        "validation": validation,
        "policy": "ROM-derived output only; color index 0 is alpha-transparent.",
    }
    (args.out_dir / "resources.json").write_text(
        json.dumps(resources, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "palette.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "mode7_composite_palette",
                "entries": palette_entries,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "mode7_rom_render_index",
                "tileset_id": args.tileset_id,
                "graphics_operand": args.gfx_operand,
                "palette_operand": args.palette_operand,
                "map_count": len(maps),
                "maps": maps,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
