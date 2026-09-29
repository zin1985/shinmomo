#!/usr/bin/env python3
"""Render SNES Mode-7/EXTBG map families from ROM setup resources only.

Graphics come from normal-VM opcode 0x10 resources.
Visible colors come from normal-VM opcode 0x11 resources.

For Mode-7 EXTBG the pixel high bit is a BG2 priority bit, not a palette bit.
For known map families BG1+BG2 are enabled on the main screen and no raw pixel
0x80 occurs, so the visible background color index is pixel & 0x7F.

Pixel value 0 is exported as alpha-transparent. Raw 0x80 is fail-closed because
BG2 color 0 would be transparent and BG1 high-CGRAM fallback would matter.
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def config_layout_ids(path: Path, tileset_id: int) -> list[int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return sorted({
        int(row["primary_layout_id"])
        for row in rows
        if int(row["primary_tileset_id"]) == tileset_id
    })


def parse_layout_palette(items: list[str] | None) -> dict[int, int]:
    out: dict[int, int] = {}
    for item in items or []:
        left, sep, right = item.partition(":")
        if not sep:
            raise ValueError(
                f"invalid --layout-palette {item!r}; expected LAYOUT:OPERAND"
            )
        layout_id = int(left, 0)
        operand = int(right, 0)
        out[layout_id] = operand
    return out


def visible_extbg_index(raw_index: int) -> int | None:
    """Return visible background color index for the proven EXTBG setup.

    BG1 and BG2 are both enabled. For values 0x81..0xFF BG2 overlays BG1,
    using the low 7 bits as color and the high bit as priority.
    0x00 is transparent. 0x80 is intentionally unsupported because BG2 color
    zero is transparent and the underlying BG1 high-CGRAM color would show.
    """
    if raw_index == 0:
        return None
    if raw_index == 0x80:
        raise ValueError(
            "raw Mode-7 pixel 0x80 requires BG1 high-CGRAM fallback; "
            "not proven for static renderer"
        )
    if raw_index & 0x80:
        return raw_index & 0x7F
    return raw_index


def build_palette(
    rom: bytes, palette_operand: int, descriptor_index: int
):
    palette, meta = normal.palette_from_opcode11(
        rom, palette_operand, descriptor_index
    )
    covered = {entry["index"] for entry in meta["entries"]}
    return palette, covered, meta


def layout_tile_ids(rom: bytes, tileset_id: int, layout_id: int):
    layout = mapdec.parse_layout(rom, layout_id)
    if layout["map_mode_low_nibble"] != 1:
        raise ValueError(
            f"layout {layout_id} has mode "
            f"{layout['map_mode_low_nibble']}, expected 1"
        )
    ptr = mapdec.tileset_pointer(rom, tileset_id)
    mids = {mid for row in layout["grid"] for mid in row}
    tile_ids = set()
    for mid in mids:
        off = 0xE0000 + ptr + mid * 4
        raw = rom[off:off + 4]
        if len(raw) != 4:
            raise ValueError(f"layout {layout_id} CE definition truncated")
        tile_ids.update(raw)
    return layout, mids, tile_ids


def validate_layout(
    graphics: bytes,
    palette_covered: set[int],
    rom: bytes,
    tileset_id: int,
    layout_id: int,
):
    _, mids, tile_ids = layout_tile_ids(rom, tileset_id, layout_id)
    raw_indices = set()
    visible_indices = set()
    priority_pixel_count = 0
    raw_80_count = 0

    for tile_id in tile_ids:
        start = tile_id * 64
        end = start + 64
        if end > len(graphics):
            raise ValueError(
                f"layout {layout_id} references tile {tile_id:#x} "
                f"outside graphics resource ({len(graphics)} bytes)"
            )
        for raw in graphics[start:end]:
            raw_indices.add(raw)
            if raw & 0x80:
                priority_pixel_count += 1
            if raw == 0x80:
                raw_80_count += 1
            visible = visible_extbg_index(raw)
            if visible is not None:
                visible_indices.add(visible)

    missing = sorted(
        index for index in visible_indices
        if index not in palette_covered
    )
    if missing:
        raise ValueError(
            f"layout {layout_id} references visible CGRAM indices outside "
            "opcode11 resource: "
            + ",".join(f"{x:#x}" for x in missing)
        )

    return {
        "metatile_id_count": len(mids),
        "tile_id_count": len(tile_ids),
        "max_tile_id": max(tile_ids) if tile_ids else None,
        "raw_color_indices": sorted(raw_indices),
        "visible_color_indices": sorted(visible_indices),
        "priority_pixel_samples_in_unique_tiles": priority_pixel_count,
        "raw_0x80_samples_in_unique_tiles": raw_80_count,
        "transparent_raw_index": 0,
        "extbg_priority_bit": 7,
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
                        raw_index = graphics[source + y * 8 + x]
                        visible = visible_extbg_index(raw_index)
                        if visible is None:
                            continue
                        out[ox + x, oy + y] = (*palette[visible], 255)
    return image


def palette_json(
    palette: list[tuple[int, int, int]],
    covered: set[int],
    meta: dict,
):
    by_index = {entry["index"]: entry for entry in meta["entries"]}
    entries = []
    for index in range(256):
        item = {
            "index": index,
            "rgb888": list(palette[index]),
            "covered": index in covered,
        }
        if index in by_index:
            item.update(by_index[index])
        entries.append(item)
    return {
        "schema_version": 2,
        "kind": "mode7_opcode11_palette",
        "operand": meta["operand"],
        "descriptor_addr": meta["descriptor_addr"],
        "destination_index": meta["destination_index"],
        "color_count": meta["color_count"],
        "entries": entries,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--tileset-id", type=int, required=True)
    ap.add_argument("--gfx-operand", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--palette-operand", type=lambda s: int(s, 0))
    ap.add_argument(
        "--layout-palette",
        action="append",
        help="per-layout palette override as LAYOUT:OPERAND, repeatable",
    )
    ap.add_argument("--state0-descriptor-index", type=int, default=2)
    ap.add_argument("--layout-id", type=int, action="append")
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    layout_palette = parse_layout_palette(args.layout_palette)
    rom = args.rom.read_bytes()

    graphics_meta = normal.graphics_descriptor(
        rom, args.gfx_operand, args.state0_descriptor_index
    )
    graphics = normal.decode_graphics_resource(
        rom, graphics_meta, args.gfx_operand
    )
    layout_ids = args.layout_id or config_layout_ids(
        args.config_index, args.tileset_id
    )

    palette_operands = {}
    for layout_id in layout_ids:
        operand = layout_palette.get(layout_id, args.palette_operand)
        if operand is None:
            raise ValueError(
                f"no palette operand for layout {layout_id}; "
                "use --palette-operand or --layout-palette"
            )
        palette_operands[layout_id] = operand

    palette_cache = {}
    for operand in sorted(set(palette_operands.values())):
        palette_cache[operand] = build_palette(
            rom, operand, args.state0_descriptor_index
        )

    validation = {}
    for layout_id in layout_ids:
        operand = palette_operands[layout_id]
        _, covered, _ = palette_cache[operand]
        validation[layout_id] = validate_layout(
            graphics, covered, rom, args.tileset_id, layout_id
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    maps = []
    for layout_id in layout_ids:
        operand = palette_operands[layout_id]
        palette, _, _ = palette_cache[operand]
        image = render_layout(
            rom, graphics, palette, args.tileset_id, layout_id
        )
        png = args.out_dir / f"map_{layout_id:03d}.png"
        image.save(png, optimize=True)
        meta = {
            "schema_version": 2,
            "tileset_id": args.tileset_id,
            "layout_id": layout_id,
            "render_mode": "snes_mode7_extbg_rom_setup",
            "image_mode": "RGBA",
            "transparent_raw_color_index": 0,
            "extbg_priority_bit": 7,
            "extbg_visible_color_rule": (
                "raw 0x01..0x7F -> same index; "
                "raw 0x81..0xFF -> raw&0x7F"
            ),
            "image_width_px": image.width,
            "image_height_px": image.height,
            "graphics_operand": args.gfx_operand,
            "palette_operand": operand,
            "validation": validation[layout_id],
            "output_png": png.name,
            "output_png_sha256": sha256_file(png),
        }
        (args.out_dir / f"map_{layout_id:03d}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        maps.append(meta)
        print(
            f"rendered EXTBG map {layout_id:03d}: {image.size} "
            f"palette=0x{operand:02X}"
        )

    palette_files = {}
    for operand, (palette, covered, meta) in palette_cache.items():
        name = (
            "palette.json" if len(palette_cache) == 1
            else f"palette_{operand:02X}.json"
        )
        (args.out_dir / name).write_text(
            json.dumps(
                palette_json(palette, covered, meta),
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        palette_files[f"0x{operand:02X}"] = name

    resources = {
        "schema_version": 2,
        "kind": "mode7_extbg_rom_resources",
        "tileset_id": args.tileset_id,
        "graphics_operand": args.gfx_operand,
        "graphics_descriptor": graphics_meta,
        "graphics_decoded_sha256": hashlib.sha256(graphics).hexdigest().upper(),
        "layout_palette_operands": {
            str(k): v for k, v in sorted(palette_operands.items())
        },
        "palette_files": palette_files,
        "ppu_proof": {
            "runtime_wram_0382": "0x40",
            "setini_extbg_bit": True,
            "runtime_wram_0379_tm": "0x03",
            "main_screen_layers": ["BG1", "BG2"],
            "runtime_wram_037a_ts": "0x00",
            "runtime_wram_037e_cgadsub": "0x23",
            "runtime_backdrop_cgram_00": "0x0000",
        },
        "validation": {
            str(k): v for k, v in sorted(validation.items())
        },
        "policy": (
            "ROM-derived output only; Mode-7 EXTBG bit7 is priority, "
            "not a palette-index bit; raw index 0 is alpha-transparent."
        ),
    }
    (args.out_dir / "resources.json").write_text(
        json.dumps(resources, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "mode7_extbg_rom_render_index",
                "tileset_id": args.tileset_id,
                "graphics_operand": args.gfx_operand,
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
