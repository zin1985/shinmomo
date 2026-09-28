#!/usr/bin/env python3
"""Render full map-layout PNGs from ROM metatiles plus a validated VRAM/CGRAM capture.

Raw ROM/VRAM/CGRAM stay local. The tool writes only derived PNG/JSON/CSV outputs.
One capture should be used only for layouts sharing the capture's tileset/CHR state.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

import decode_map_layout as mapdec


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_CONFIG_INDEX = REPO / "data/maps/configurations/map_configuration_index.csv"
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def decode_4bpp_tile(vram: bytes, char_base: int, tile_index: int) -> list[list[int]]:
    base = char_base + tile_index * 32
    if base < 0 or base + 32 > len(vram):
        raise ValueError(f"tile {tile_index:#x} outside VRAM at {base:#x}")
    out = [[0] * 8 for _ in range(8)]
    for y in range(8):
        p0 = vram[base + y * 2]
        p1 = vram[base + y * 2 + 1]
        p2 = vram[base + 16 + y * 2]
        p3 = vram[base + 16 + y * 2 + 1]
        for x in range(8):
            bit = 7 - x
            out[y][x] = (
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
            )
    return out
def decode_cgram(cgram: bytes) -> list[tuple[int, int, int]]:
    if len(cgram) < 512:
        raise ValueError(f"CGRAM too short: {len(cgram)}")
    colors: list[tuple[int, int, int]] = []
    for i in range(256):
        word = cgram[i * 2] | (cgram[i * 2 + 1] << 8)
        r5 = word & 0x1F
        g5 = (word >> 5) & 0x1F
        b5 = (word >> 10) & 0x1F
        colors.append((
            round(r5 * 255 / 31),
            round(g5 * 255 / 31),
            round(b5 * 255 / 31),
        ))
    return colors


def read_config_rows(path: Path, tileset_id: int) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["primary_tileset_id"]) != tileset_id:
                continue
            layout_id = int(row["primary_layout_id"])
            grouped.setdefault(layout_id, []).append(row)
    return grouped
def render_expanded(
    expanded: list[list[int]],
    vram: bytes,
    palette: list[tuple[int, int, int]] | None,
    char_base: int,
) -> Image.Image:
    tile_cache: dict[int, list[list[int]]] = {}
    h_tiles = len(expanded)
    w_tiles = len(expanded[0])
    image = Image.new("RGB", (w_tiles * 8, h_tiles * 8))
    pixels = image.load()

    for ty, row in enumerate(expanded):
        for tx, entry in enumerate(row):
            tile_index = entry & 0x03FF
            palette_id = (entry >> 10) & 0x07
            hflip = bool(entry & 0x4000)
            vflip = bool(entry & 0x8000)
            if tile_index not in tile_cache:
                tile_cache[tile_index] = decode_4bpp_tile(vram, char_base, tile_index)
            tile = tile_cache[tile_index]
            for py in range(8):
                sy = 7 - py if vflip else py
                for px in range(8):
                    sx = 7 - px if hflip else px
                    color_index = tile[sy][sx]
                    if palette is None:
                        value = color_index * 17
                        pixels[tx * 8 + px, ty * 8 + py] = (value, value, value)
                    else:
                        cgram_index = palette_id * 16 + color_index
                        pixels[tx * 8 + px, ty * 8 + py] = palette[cgram_index]
    return image
def render_one(
    rom: bytes,
    vram: bytes,
    palette: list[tuple[int, int, int]] | None,
    tileset_id: int,
    layout_id: int,
    char_base: int,
) -> tuple[Image.Image, dict]:
    layout = mapdec.parse_layout(rom, layout_id)
    expanded_info = mapdec.expand_tileset(rom, layout["grid"], tileset_id)
    expanded = expanded_info["expanded"]
    image = render_expanded(expanded, vram, palette, char_base)
    meta = {
        "tileset_id": tileset_id,
        "layout_id": layout_id,
        "layout_flags": layout["flags"],
        "layout_width_chunks": layout["width_chunks"],
        "layout_height_chunks": layout["height_chunks"],
        "cell_count": layout["cell_count"],
        "expanded_width_tiles": len(expanded[0]),
        "expanded_height_tiles": len(expanded),
        "image_width_px": image.width,
        "image_height_px": image.height,
    }
    return image, meta


def load_capture_manifest(capture_dir: Path) -> dict:
    manifest = capture_dir / "manifest.json"
    if not manifest.exists():
        return {}
    return json.loads(manifest.read_text(encoding="utf-8-sig"))
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("capture_dir", type=Path)
    ap.add_argument("--tileset-id", type=int, required=True)
    ap.add_argument("--char-base", type=lambda v: int(v, 0), default=0x8000)
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG_INDEX)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    vram_path = args.capture_dir / "vram.bin"
    cgram_path = args.capture_dir / "cgram.bin"
    vram = vram_path.read_bytes()
    cgram = cgram_path.read_bytes()
    if len(set(cgram)) <= 1:
        palette = None
        palette_mode = "tile_index_grayscale"
    else:
        palette = decode_cgram(cgram)
        palette_mode = "captured_cgram"
    manifest = load_capture_manifest(args.capture_dir)
    grouped = read_config_rows(args.config_index, args.tileset_id)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    capture_id = manifest.get("capture_id", args.capture_dir.name)
    source_hashes = {
        "vram_sha256": sha256_file(vram_path),
        "cgram_sha256": sha256_file(cgram_path),
    }
    for layout_id in sorted(grouped):
        image, meta = render_one(
            rom, vram, palette, args.tileset_id, layout_id, args.char_base
        )
        png_name = f"map_{layout_id:03d}.png"
        json_name = f"map_{layout_id:03d}.json"
        png_path = args.out_dir / png_name
        json_path = args.out_dir / json_name
        image.save(png_path, optimize=True)

        configs = grouped[layout_id]
        meta.update({
            "capture_id": capture_id,
            "char_base": f"0x{args.char_base:04X}",
            "bpp": 4,
            "palette_mode": palette_mode,
            "source_hashes": source_hashes,
            "config_ids": [r["config_id"] for r in configs],
            "pack_ids_hex": sorted({
                p for r in configs for p in r["pack_ids_hex"].split(";") if p
            }),
            "command_addresses": sorted({
                p for r in configs for p in r["command_addresses"].split(";") if p
            }),
            "output_png": png_name,
            "output_png_sha256": sha256_file(png_path),
        })
        json_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        rows.append(meta)
        print(f"rendered map {layout_id:03d}: {image.width}x{image.height}")
    index_json = {
        "schema_version": 1,
        "kind": "derived_map_layout_render_index",
        "tileset_id": args.tileset_id,
        "capture_id": capture_id,
        "char_base": f"0x{args.char_base:04X}",
        "bpp": 4,
        "palette_mode": palette_mode,
        "source_hashes": source_hashes,
        "map_count": len(rows),
        "maps": rows,
        "policy": "Raw ROM/VRAM/CGRAM are local-only; only derived renders and hashes are canonical.",
    }
    (args.out_dir / "index.json").write_text(
        json.dumps(index_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "layout_id", "tileset_id", "layout_flags",
        "layout_width_chunks", "layout_height_chunks", "cell_count",
        "image_width_px", "image_height_px", "capture_id",
        "char_base", "bpp", "palette_mode", "output_png", "output_png_sha256",
        "config_ids", "pack_ids_hex", "command_addresses",
    ]
    with (args.out_dir / "index.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **{k: row.get(k, "") for k in fieldnames},
                "config_ids": ";".join(row["config_ids"]),
                "pack_ids_hex": ";".join(row["pack_ids_hex"]),
                "command_addresses": ";".join(row["command_addresses"]),
            })
    print(f"done: {len(rows)} maps -> {args.out_dir}")


if __name__ == "__main__":
    main()
