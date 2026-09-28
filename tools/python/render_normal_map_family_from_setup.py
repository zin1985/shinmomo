#!/usr/bin/env python3
"""Render normal 4bpp map families directly from ROM setup opcodes.

This reconstructs the graphics resources selected by normal-VM opcode 0x10 and
the CGRAM range selected by opcode 0x11, then renders the selected map layouts.
No runtime VRAM/CGRAM dump is required.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

import decode_map_layout as mapdec
from render_map_layout_images import decode_4bpp_tile


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"


def file_off(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | (addr & 0xFFFF)


def u16_cpu(rom: bytes, bank: int, addr: int) -> int:
    off = file_off(bank, addr)
    return rom[off] | (rom[off + 1] << 8)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())
def state0_descriptor_base(rom: bytes, descriptor_index: int) -> int:
    """Return the C3 descriptor base selected through C0:BAAC[$035F]."""
    return u16_cpu(rom, 0xC0, 0xBAAC + descriptor_index * 2)


def graphics_descriptor(rom: bytes, operand: int, descriptor_index: int) -> dict:
    base = state0_descriptor_base(rom, descriptor_index)
    addr = base + (operand - 1) * 8
    off = file_off(0xC3, addr)
    raw = rom[off : off + 8]
    if len(raw) != 8:
        raise ValueError("graphics descriptor truncated")
    vram_word = raw[0] | (raw[1] << 8)
    output_size = raw[2] | (raw[3] << 8)
    source_addr = raw[4] | (raw[5] << 8)
    source_bank = raw[6]
    mode_byte = raw[7]
    return {
        "operand": operand,
        "descriptor_addr": f"C3:{addr:04X}",
        "descriptor_raw": raw.hex(" "),
        "vram_word_addr": vram_word,
        "vram_byte_addr": vram_word * 2,
        "output_size": output_size,
        "source_bank": source_bank,
        "source_addr": source_addr,
        "source": f"{source_bank:02X}:{source_addr:04X}",
        "reader_kind": mode_byte & 0x0F,
        "reader_dispatch_index": (mode_byte & 0xF0) >> 3,
    }
def decode_context4(rom: bytes, bank: int, addr: int, output_size: int) -> bytes:
    """Decode the C0:C03C/C07F four-context byte reuse stream."""
    p = file_off(bank, addr)
    previous = [0, 0, 0, 0]
    control = rom[p]
    p += 1
    mask = 0x80
    out = bytearray()
    for i in range(output_size):
        context = (i & 1) | ((i & 0x10) >> 3)
        if control & mask:
            previous[context] = rom[p]
            p += 1
        out.append(previous[context])
        mask >>= 1
        if mask == 0:
            mask = 0x80
            control = rom[p]
            p += 1
    return bytes(out)


def reconstruct_vram(rom: bytes, operands: list[int], descriptor_index: int):
    vram = bytearray(0x10000)
    resources = []
    for operand in operands:
        desc = graphics_descriptor(rom, operand, descriptor_index)
        if desc["reader_dispatch_index"] != 2:
            raise ValueError(
                f"opcode10 operand {operand:#x}: unsupported reader dispatch "
                f"{desc['reader_dispatch_index']}"
            )
        decoded = decode_context4(
            rom,
            desc["source_bank"],
            desc["source_addr"],
            desc["output_size"],
        )
        start = desc["vram_byte_addr"]
        end = start + len(decoded)
        if end > len(vram):
            raise ValueError("decoded graphics exceeds VRAM")
        vram[start:end] = decoded
        desc["decoded_sha256"] = sha256_bytes(decoded)
        desc["decoded_end_byte"] = end
        resources.append(desc)
    return bytes(vram), resources
def palette_from_opcode11(rom: bytes, operand: int, descriptor_index: int):
    table = u16_cpu(rom, 0xC0, 0xB516 + descriptor_index * 2)
    entry_ptr = u16_cpu(rom, 0xC0, table + (operand - 1) * 2)
    desc_off = file_off(0xC0, entry_ptr)
    destination = rom[desc_off] | (rom[desc_off + 1] << 8)
    count = rom[desc_off + 2] | (rom[desc_off + 3] << 8)
    payload_off = desc_off + 4

    palette = [(0, 0, 0)] * 256
    entries = []
    for i in range(count):
        word = rom[payload_off + i * 2] | (rom[payload_off + i * 2 + 1] << 8)
        rgb = (
            round((word & 0x1F) * 255 / 31),
            round(((word >> 5) & 0x1F) * 255 / 31),
            round(((word >> 10) & 0x1F) * 255 / 31),
        )
        index = destination + i
        if index >= 256:
            raise ValueError("palette descriptor exceeds CGRAM")
        palette[index] = rgb
        entries.append({
            "index": index,
            "bgr555": f"0x{word:04X}",
            "rgb888": list(rgb),
        })

    meta = {
        "operand": operand,
        "state0_descriptor_index": descriptor_index,
        "first_level_table": f"C0:{table:04X}",
        "descriptor_addr": f"C0:{entry_ptr:04X}",
        "destination_index": destination,
        "color_count": count,
        "payload_addr": f"C0:{(entry_ptr + 4) & 0xFFFF:04X}",
        "entries": entries,
    }
    return palette, meta
def config_rows(path: Path, tileset_id: int):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [r for r in rows if int(r["primary_tileset_id"]) == tileset_id]


def render_rgba(expanded, vram: bytes, palette):
    height = len(expanded) * 8
    width = len(expanded[0]) * 8
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    cache = {}

    for ty, row in enumerate(expanded):
        for tx, entry in enumerate(row):
            tile_id = entry & 0x03FF
            palette_id = (entry >> 10) & 0x07
            hflip = bool(entry & 0x4000)
            vflip = bool(entry & 0x8000)
            if tile_id not in cache:
                cache[tile_id] = decode_4bpp_tile(vram, 0, tile_id)
            tile = cache[tile_id]
            for py in range(8):
                sy = 7 - py if vflip else py
                for px in range(8):
                    sx = 7 - px if hflip else px
                    color_index = tile[sy][sx]
                    # SNES normal BG color 0 is transparent.
                    if color_index == 0:
                        continue
                    rgb = palette[palette_id * 16 + color_index]
                    pixels[tx * 8 + px, ty * 8 + py] = (*rgb, 255)
    return image
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--tileset-id", type=int, required=True)
    ap.add_argument("--gfx-operand", type=lambda x: int(x, 0), action="append", required=True)
    ap.add_argument("--palette-operand", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--descriptor-index", type=int, default=2)
    ap.add_argument("--layout-id", type=int, action="append")
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    vram, resources = reconstruct_vram(
        rom, args.gfx_operand, args.descriptor_index
    )
    palette, palette_meta = palette_from_opcode11(
        rom, args.palette_operand, args.descriptor_index
    )

    rows = config_rows(args.config_index, args.tileset_id)
    layout_ids = args.layout_id or sorted({
        int(r["primary_layout_id"]) for r in rows
    })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    maps = []
    for layout_id in layout_ids:
        expanded = mapdec.expand_tileset(
            rom,
            mapdec.parse_layout(rom, layout_id)["grid"],
            args.tileset_id,
        )["expanded"]
        image = render_rgba(expanded, vram, palette)
        png = args.out_dir / f"map_{layout_id:03d}.png"
        image.save(png, optimize=True)
        related = [r for r in rows if int(r["primary_layout_id"]) == layout_id]
        meta = {
            "tileset_id": args.tileset_id,
            "layout_id": layout_id,
            "render_mode": "normal_4bpp_rom_setup",
            "transparent_color_index_zero": True,
            "graphics_operands": args.gfx_operand,
            "palette_operand": args.palette_operand,
            "state0_descriptor_index": args.descriptor_index,
            "config_ids": sorted({r["config_id"] for r in related}),
            "pack_ids_hex": sorted({
                p
                for r in related
                for p in (r.get("pack_ids_hex") or "").split(";")
                if p
            }),
            "output_png": png.name,
            "output_png_sha256": sha256_file(png),
        }
        (args.out_dir / f"map_{layout_id:03d}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        maps.append(meta)
        print(f"rendered map {layout_id:03d}: {image.size}")

    resources_doc = {
        "schema_version": 1,
        "kind": "rom_map_setup_resources",
        "tileset_id": args.tileset_id,
        "state0_descriptor_index": args.descriptor_index,
        "graphics_resources": resources,
        "palette_resource": palette_meta,
    }
    (args.out_dir / "resources.json").write_text(
        json.dumps(resources_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "palette.json").write_text(
        json.dumps({
            "schema_version": 1,
            "kind": "rom_opcode11_palette",
            **palette_meta,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out_dir / "index.json").write_text(
        json.dumps({
            "schema_version": 1,
            "kind": "normal_4bpp_map_family_render_index",
            "tileset_id": args.tileset_id,
            "graphics_operands": args.gfx_operand,
            "palette_operand": args.palette_operand,
            "map_count": len(maps),
            "maps": maps,
            "policy": "Derived entirely from ROM; normal-BG color index 0 is transparent.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
