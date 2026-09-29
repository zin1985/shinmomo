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


def decode_ring_lzss(rom: bytes, bank: int, addr: int, output_size: int) -> bytes:
    """Decode graphics reader dispatch 0 (C0:BCEE/BD28).

    The runtime reader uses a 256-byte dictionary page initially filled with
    zeroes.  The write cursor starts at 0xEF.  Flag bits are consumed MSB-first:
    bit 1 emits one literal byte, while bit 0 reads an 8-bit dictionary offset.
    One length byte is shared by each pair of back-references.  The runtime
    stores nibble+1 in $7D, immediately copies one byte at BD2E, and decrements
    $7D only on later reader calls, so the effective copy length is nibble+2
    (2..17 bytes), not nibble+1.
    """
    p = file_off(bank, addr)
    ring = bytearray(256)
    write_pos = 0xEF

    control = 0
    bits_left = 0
    length_pair = 0
    use_low_nibble = False

    out = bytearray()
    while len(out) < output_size:
        if bits_left == 0:
            if p >= len(rom):
                raise ValueError("dispatch-0 stream truncated at flag byte")
            control = rom[p]
            p += 1
            bits_left = 8

        literal = bool(control & 0x80)
        control = (control << 1) & 0xFF
        bits_left -= 1

        if p >= len(rom):
            raise ValueError("dispatch-0 stream truncated at token byte")
        value = rom[p]
        p += 1

        if literal:
            out.append(value)
            ring[write_pos] = value
            write_pos = (write_pos + 1) & 0xFF
            continue

        read_pos = value
        if not use_low_nibble:
            if p >= len(rom):
                raise ValueError("dispatch-0 stream truncated at length byte")
            length_pair = rom[p]
            p += 1
            copy_len = (length_pair >> 4) + 2
            use_low_nibble = True
        else:
            copy_len = (length_pair & 0x0F) + 2
            use_low_nibble = False

        for _ in range(copy_len):
            value = ring[read_pos]
            read_pos = (read_pos + 1) & 0xFF
            out.append(value)
            ring[write_pos] = value
            write_pos = (write_pos + 1) & 0xFF
            if len(out) == output_size:
                break

    return bytes(out)


def decode_graphics_resource(rom: bytes, desc: dict, operand: int) -> bytes:
    dispatch = desc["reader_dispatch_index"]
    if dispatch == 0:
        return decode_ring_lzss(
            rom,
            desc["source_bank"],
            desc["source_addr"],
            desc["output_size"],
        )
    if dispatch == 2:
        return decode_context4(
            rom,
            desc["source_bank"],
            desc["source_addr"],
            desc["output_size"],
        )
    raise ValueError(
        f"graphics operand {operand:#x}: unsupported reader dispatch {dispatch}"
    )


def reconstruct_vram(
    rom: bytes,
    operands: list[int],
    descriptor_index: int,
    overrides: list[tuple[int, int]] | None = None,
):
    vram = bytearray(0x10000)
    resources = []
    placements = [(operand, None) for operand in operands]
    placements.extend((operand, word_addr) for operand, word_addr in (overrides or []))
    for operand, override_word_addr in placements:
        desc = graphics_descriptor(rom, operand, descriptor_index)
        decoded = decode_graphics_resource(rom, desc, operand)
        desc["descriptor_vram_word_addr"] = desc["vram_word_addr"]
        desc["descriptor_vram_byte_addr"] = desc["vram_byte_addr"]
        if override_word_addr is None:
            desc["placement_source"] = "opcode10_descriptor_destination"
        else:
            desc["placement_source"] = "opcode33_explicit_destination"
            desc["vram_word_addr"] = override_word_addr
            desc["vram_byte_addr"] = override_word_addr * 2
        start = desc["vram_byte_addr"]
        end = start + len(decoded)
        if end > len(vram):
            raise ValueError("decoded graphics exceeds VRAM")
        vram[start:end] = decoded
        desc["decoded_sha256"] = sha256_bytes(decoded)
        desc["decoded_end_byte"] = end
        resources.append(desc)
    return bytes(vram), resources


def parse_gfx_override(value: str) -> tuple[int, int]:
    try:
        operand_text, word_addr_text = value.split("@", 1)
        return int(operand_text, 0), int(word_addr_text, 0)
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            "graphics override must be OPERAND@VRAM_WORD, e.g. 0x0F@0x1000"
        ) from exc


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


def validate_layout_resources(expanded, vram: bytes, resources, palette_meta):
    loaded = [
        (r["vram_byte_addr"], r["decoded_end_byte"])
        for r in resources
    ]
    missing_tiles = set()
    used_tiles = set()
    used_palette_indices = set()
    cache = {}

    for row in expanded:
        for entry in row:
            tile_id = entry & 0x03FF
            palette_id = (entry >> 10) & 0x07
            used_tiles.add(tile_id)
            start = tile_id * 32
            end = start + 32
            if not any(a <= start and end <= b for a, b in loaded):
                missing_tiles.add(tile_id)
                continue
            if tile_id not in cache:
                cache[tile_id] = decode_4bpp_tile(vram, 0, tile_id)
            for line in cache[tile_id]:
                for color_index in line:
                    if color_index:
                        used_palette_indices.add(
                            palette_id * 16 + color_index
                        )

    first = palette_meta["destination_index"]
    last = first + palette_meta["color_count"]
    missing_palette = sorted(
        i for i in used_palette_indices
        if not (first <= i < last)
    )
    if missing_tiles:
        raise ValueError(
            "layout references CHR outside setup resources: "
            + ",".join(f"{x:#x}" for x in sorted(missing_tiles))
        )
    if missing_palette:
        raise ValueError(
            "layout references palette entries outside opcode11 resource: "
            + ",".join(f"{x:#x}" for x in missing_palette)
        )

    return {
        "used_tile_ids": sorted(used_tiles),
        "used_palette_indices_nonzero": sorted(used_palette_indices),
        "graphics_resource_coverage_complete": True,
        "palette_resource_coverage_complete": True,
    }


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
    ap.add_argument("--gfx-operand", type=lambda x: int(x, 0), action="append", default=[])
    ap.add_argument(
        "--gfx-override",
        type=parse_gfx_override,
        action="append",
        default=[],
        help="opcode-0x33 resource as OPERAND@VRAM_WORD, e.g. 0x0F@0x1000",
    )
    ap.add_argument("--palette-operand", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--descriptor-index", type=int, default=2)
    ap.add_argument("--layout-id", type=int, action="append")
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    if not args.gfx_operand and not args.gfx_override:
        ap.error("at least one --gfx-operand or --gfx-override is required")

    rom = args.rom.read_bytes()
    vram, resources = reconstruct_vram(
        rom,
        args.gfx_operand,
        args.descriptor_index,
        args.gfx_override,
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
        coverage = validate_layout_resources(
            expanded, vram, resources, palette_meta
        )
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
            "graphics_overrides": [
                {"operand": operand, "vram_word_addr": word_addr}
                for operand, word_addr in args.gfx_override
            ],
            "palette_operand": args.palette_operand,
            "state0_descriptor_index": args.descriptor_index,
            **coverage,
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
            "graphics_overrides": [
                {"operand": operand, "vram_word_addr": word_addr}
                for operand, word_addr in args.gfx_override
            ],
            "palette_operand": args.palette_operand,
            "map_count": len(maps),
            "maps": maps,
            "policy": "Derived entirely from ROM; normal-BG color index 0 is transparent.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
