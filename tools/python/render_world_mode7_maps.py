#!/usr/bin/env python3
"""Render mode-7 world layouts from ROM definitions plus validated runtime VRAM/palette."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

import decode_map_layout as mapdec
from render_map_layout_images import decode_cgram, load_wram_palette_capture


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()
def decode_mode7_tiles(vram: bytes, palette: list[tuple[int, int, int]]):
    """SNES Mode 7 stores tile pixels in the odd byte of each VRAM word."""
    pixels = vram[1::2]
    if len(pixels) < 256 * 64:
        raise ValueError("VRAM is too short for 256 Mode-7 tiles")
    tiles = []
    for tile_id in range(256):
        base = tile_id * 64
        tile = [
            [palette[pixels[base + y * 8 + x]] for x in range(8)]
            for y in range(8)
        ]
        tiles.append(tile)
    return tiles


def world_layout_ids(config_path: Path, tileset_id: int) -> list[int]:
    ids = set()
    with config_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if int(row["primary_tileset_id"]) != tileset_id:
                continue
            ids.add(int(row["primary_layout_id"]))
    return sorted(ids)
def render_world_layout(
    rom: bytes,
    tiles: list[list[list[tuple[int, int, int]]]],
    tileset_id: int,
    layout_id: int,
) -> tuple[Image.Image, dict]:
    layout = mapdec.parse_layout(rom, layout_id)
    if layout["map_mode_low_nibble"] != 1:
        raise ValueError(
            f"layout {layout_id} mode is {layout['map_mode_low_nibble']}, expected 1"
        )

    ptr = mapdec.tileset_pointer(rom, tileset_id)
    next_ptr = mapdec.tileset_next_pointer(rom, tileset_id)
    max_id = max(max(row) for row in layout["grid"])
    if next_ptr is not None and ptr + (max_id + 1) * 4 > next_ptr:
        raise ValueError(
            f"world definition id {max_id} exceeds CE block "
            f"{ptr:04X}..{next_ptr:04X}"
        )

    width = len(layout["grid"][0]) * 16
    height = len(layout["grid"]) * 16
    image = Image.new("RGB", (width, height))
    out = image.load()
    for my, row in enumerate(layout["grid"]):
        for mx, metatile_id in enumerate(row):
            base = 0xE0000 + ptr + metatile_id * 4
            tile_ids = rom[base : base + 4]
            if len(tile_ids) != 4:
                raise ValueError("world CE definition truncated")
            for quadrant, tile_id in enumerate(tile_ids):
                ox = mx * 16 + (quadrant & 1) * 8
                oy = my * 16 + (quadrant >> 1) * 8
                tile = tiles[tile_id]
                for y in range(8):
                    for x in range(8):
                        out[ox + x, oy + y] = tile[y][x]

    meta = {
        "tileset_id": tileset_id,
        "layout_id": layout_id,
        "layout_flags": layout["flags"],
        "map_mode_low_nibble": layout["map_mode_low_nibble"],
        "definition_bytes_per_id": 4,
        "definition_block_ptr": f"CE:{ptr:04X}",
        "max_definition_id": max_id,
        "image_width_px": image.width,
        "image_height_px": image.height,
        "render_mode": "snes_mode7",
    }
    return image, meta
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("vram", type=Path)
    ap.add_argument("palette_wram_json", type=Path)
    ap.add_argument("--tileset-id", type=int, default=1)
    ap.add_argument("--layout-id", type=int, action="append")
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    vram = args.vram.read_bytes()
    palette_bytes, palette_source = load_wram_palette_capture(
        args.palette_wram_json
    )
    palette = decode_cgram(palette_bytes)
    tiles = decode_mode7_tiles(vram, palette)
    layout_ids = args.layout_id or world_layout_ids(
        args.config_index, args.tileset_id
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    maps = []
    for layout_id in layout_ids:
        image, meta = render_world_layout(
            rom, tiles, args.tileset_id, layout_id
        )
        png = args.out_dir / f"map_{layout_id:03d}.png"
        image.save(png, optimize=True)
        meta.update({
            "output_png": png.name,
            "output_png_sha256": sha256_file(png),
        })
        (args.out_dir / f"map_{layout_id:03d}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        maps.append(meta)
        print(f"rendered world map {layout_id:03d}: {image.size}")

    index = {
        "schema_version": 1,
        "kind": "mode7_world_render_index",
        "tileset_id": args.tileset_id,
        "palette_source": palette_source,
        "vram_sha256": sha256_file(args.vram),
        "map_count": len(maps),
        "maps": maps,
        "policy": "Raw ROM/VRAM/WRAM captures remain local-only.",
    }
    (args.out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    palette_catalog = {
        "schema_version": 1,
        "kind": "derived_snes_palette",
        "source": palette_source,
        "entries": [],
    }
    for i, rgb in enumerate(palette):
        word = palette_bytes[i * 2] | (palette_bytes[i * 2 + 1] << 8)
        palette_catalog["entries"].append({
            "index": i,
            "bgr555": f"0x{word:04X}",
            "rgb888": list(rgb),
        })
    (args.out_dir / "palette.json").write_text(
        json.dumps(palette_catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
