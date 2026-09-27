#!/usr/bin/env python3
"""Reconstruct SNES BG tilemaps/metatiles from a Shinmomo remote-lab map capture.

Input directory is produced by:
  tools/remote_lab/shinmomo_lab.ps1 map-capture -SceneTag <tag>

Raw VRAM/CGRAM/OAM stay outside Git. This tool emits derived metadata, decoded
BG tilemaps, 2x2 metatile dictionaries and PPM previews suitable for validation.
No third-party Python package is required.

Important:
- PPU register values are a write mirror captured after the remote bridge starts.
- A scene should be entered after the bridge is active so BGMODE/BGnSC/BGnNBA
  writes are observed.
- This reconstructs the *currently resident BG tilemap*. It is not yet proof of
  the ROM-side canonical map storage/compression format.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


PPU = {
    "BGMODE": "2105",
    "BG1SC": "2107",
    "BG2SC": "2108",
    "BG3SC": "2109",
    "BG4SC": "210A",
    "BG12NBA": "210B",
    "BG34NBA": "210C",
    "TM": "212C",
    "TS": "212D",
}


def ppu_value(manifest: dict, key: str) -> int | None:
    value = manifest.get("ppu", {}).get(PPU[key])
    return value if isinstance(value, int) else None


def bg_bpp(mode: int, bg: int) -> int:
    if mode == 0:
        return 2
    if mode == 1:
        return 2 if bg == 3 else 4
    if mode == 2:
        return 4
    if mode == 3:
        return 8 if bg == 1 else 4
    if mode == 4:
        return 8 if bg == 1 else 2
    if mode == 5:
        return 4 if bg == 1 else 2
    if mode == 6:
        return 4
    if mode == 7:
        return 8
    return 4


def bg_dims(sc: int) -> tuple[int, int]:
    size = sc & 0x03
    return {
        0: (32, 32),
        1: (64, 32),
        2: (32, 64),
        3: (64, 64),
    }[size]


def tilemap_addr(base: int, tx: int, ty: int, width: int, height: int) -> int:
    sx, sy = tx // 32, ty // 32
    ix, iy = tx % 32, ty % 32
    if width == 64 and height == 32:
        screen = sx
    elif width == 32 and height == 64:
        screen = sy
    elif width == 64 and height == 64:
        screen = sy * 2 + sx
    else:
        screen = 0
    return (base + screen * 0x800 + (iy * 32 + ix) * 2) & 0xFFFF


def char_base(manifest: dict, bg: int) -> int | None:
    if bg <= 2:
        reg = ppu_value(manifest, "BG12NBA")
        if reg is None:
            return None
        nib = (reg & 0x0F) if bg == 1 else ((reg >> 4) & 0x0F)
    else:
        reg = ppu_value(manifest, "BG34NBA")
        if reg is None:
            return None
        nib = (reg & 0x0F) if bg == 3 else ((reg >> 4) & 0x0F)
    return (nib << 12) & 0xFFFF


def tile_pixel(vram: bytes, base: int, tile_num: int, bpp: int, x: int, y: int) -> int:
    tile_size = {2: 16, 4: 32, 8: 64}.get(bpp, 32)
    addr = (base + tile_num * tile_size) & 0xFFFF
    bit = 7 - x

    def b(off: int) -> int:
        return vram[(addr + off) & 0xFFFF]

    color = ((b(y * 2) >> bit) & 1) | (((b(y * 2 + 1) >> bit) & 1) << 1)
    if bpp >= 4:
        color |= (((b(16 + y * 2) >> bit) & 1) << 2)
        color |= (((b(16 + y * 2 + 1) >> bit) & 1) << 3)
    if bpp >= 8:
        color |= (((b(32 + y * 2) >> bit) & 1) << 4)
        color |= (((b(32 + y * 2 + 1) >> bit) & 1) << 5)
        color |= (((b(48 + y * 2) >> bit) & 1) << 6)
        color |= (((b(48 + y * 2 + 1) >> bit) & 1) << 7)
    return color


def cgram_palette(cgram: bytes) -> list[tuple[int, int, int]]:
    out = []
    for i in range(256):
        raw = cgram[i * 2] | (cgram[i * 2 + 1] << 8)
        r = raw & 0x1F
        g = (raw >> 5) & 0x1F
        b = (raw >> 10) & 0x1F
        out.append((r * 255 // 31, g * 255 // 31, b * 255 // 31))
    return out


def write_ppm(path: Path, width: int, height: int, pixels: bytearray) -> None:
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + bytes(pixels))


def decode_bg(
    capture_dir: Path,
    out_dir: Path,
    manifest: dict,
    vram: bytes,
    cgram: bytes,
    bg: int,
) -> dict | None:
    mode = ppu_value(manifest, "BGMODE")
    sc = ppu_value(manifest, f"BG{bg}SC")
    cb = char_base(manifest, bg)
    if mode is None or sc is None or cb is None:
        return None

    width, height = bg_dims(sc)
    map_base = (sc & 0xFC) << 8
    bpp = bg_bpp(mode & 0x07, bg)
    palette = cgram_palette(cgram)
    if not any(cgram):
        palette = [(i, i, i) for i in range(256)]

    rows = []
    grid: dict[tuple[int, int], int] = {}
    rendered_key: dict[tuple[int, int], tuple[int, int, int, int, int]] = {}

    for ty in range(height):
        for tx in range(width):
            addr = tilemap_addr(map_base, tx, ty, width, height)
            entry = vram[addr] | (vram[(addr + 1) & 0xFFFF] << 8)
            tile = entry & 0x03FF
            palno = (entry >> 10) & 0x07
            priority = (entry >> 13) & 1
            hflip = (entry >> 14) & 1
            vflip = (entry >> 15) & 1
            rows.append({
                "bg": bg, "tx": tx, "ty": ty, "vram_addr": f"0x{addr:04X}",
                "entry_hex": f"0x{entry:04X}", "tile": tile, "palette": palno,
                "priority": priority, "hflip": hflip, "vflip": vflip,
                "map_base": f"0x{map_base:04X}", "char_base": f"0x{cb:04X}",
                "bpp": bpp, "mode": mode & 0x07,
            })
            grid[(tx, ty)] = entry
            rendered_key[(tx, ty)] = (tile, palno, priority, hflip, vflip)

    csv_path = out_dir / f"bg{bg}_tilemap.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    metatile_counts: Counter[tuple[int, int, int, int]] = Counter()
    for y in range(height - 1):
        for x in range(width - 1):
            mt = (grid[(x, y)], grid[(x + 1, y)], grid[(x, y + 1)], grid[(x + 1, y + 1)])
            metatile_counts[mt] += 1

    meta_path = out_dir / f"bg{bg}_metatile_2x2.csv"
    with meta_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metatile_id", "count", "entry00_hex", "entry01_hex", "entry10_hex", "entry11_hex"])
        for idx, (mt, count) in enumerate(metatile_counts.most_common(), 1):
            w.writerow([f"bg{bg}_mt_{idx:04d}", count, *(f"0x{x:04X}" for x in mt)])

    pw, ph = width * 8, height * 8
    pix = bytearray(pw * ph * 3)
    for ty in range(height):
        for tx in range(width):
            tile, palno, _, hf, vf = rendered_key[(tx, ty)]
            pal_base = palno * (4 if bpp == 2 else 16 if bpp == 4 else 1)
            for py in range(8):
                for px in range(8):
                    sx = 7 - px if hf else px
                    sy = 7 - py if vf else py
                    ci = tile_pixel(vram, cb, tile, bpp, sx, sy)
                    rgb = (0, 0, 0) if ci == 0 else palette[(pal_base + ci) & 0xFF]
                    q = ((ty * 8 + py) * pw + (tx * 8 + px)) * 3
                    pix[q:q+3] = bytes(rgb)
    write_ppm(out_dir / f"bg{bg}_preview.ppm", pw, ph, pix)

    return {
        "bg": bg,
        "mode": mode & 0x07,
        "screen_size_tiles": [width, height],
        "map_base": f"0x{map_base:04X}",
        "char_base": f"0x{cb:04X}",
        "bpp": bpp,
        "unique_tilemap_entries": len(set(grid.values())),
        "unique_2x2_metatiles": len(metatile_counts),
        "tilemap_csv": csv_path.name,
        "metatile_csv": meta_path.name,
        "preview": f"bg{bg}_preview.ppm",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("capture_dir", type=Path)
    ap.add_argument("--out-dir", type=Path)
    args = ap.parse_args()

    capture_dir = args.capture_dir
    out_dir = args.out_dir or capture_dir / "derived"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((capture_dir / "manifest.json").read_text(encoding="utf-8"))
    vram = (capture_dir / "vram.bin").read_bytes()
    cgram_path = capture_dir / "cgram.bin"
    cgram = cgram_path.read_bytes() if cgram_path.exists() else bytes(0x200)

    if len(vram) != 0x10000:
        raise SystemExit(f"unexpected VRAM size: {len(vram)}")
    if len(cgram) != 0x200:
        raise SystemExit(f"unexpected CGRAM size: {len(cgram)}")
    cgram_available = cgram_path.exists()

    scene = {
        "schema_version": 1,
        "capture_id": manifest.get("capture_id"),
        "scene_tag": manifest.get("scene_tag"),
        "frame": manifest.get("frame"),
        "capture_manifest": str(capture_dir / "manifest.json"),
        "ppu_mirror_complete_for_core_bg_regs": all(
            ppu_value(manifest, k) is not None
            for k in ["BGMODE", "BG1SC", "BG2SC", "BG3SC", "BG4SC", "BG12NBA", "BG34NBA"]
        ),
        "backgrounds": [],
        "cgram_available": cgram_available,
        "limitations": [
            "runtime-resident tilemap only; canonical ROM-side map storage not yet identified",
            "PPU register values are bridge-lifetime write mirrors",
            "collision/warp/event layers require separate game-logic extraction",
            "when CGRAM domain is unavailable, preview colors are placeholders but tilemap/metatile structure remains valid",
        ],
    }

    for bg in range(1, 5):
        decoded = decode_bg(capture_dir, out_dir, manifest, vram, cgram, bg)
        if decoded:
            scene["backgrounds"].append(decoded)

    (out_dir / "scene_summary.json").write_text(
        json.dumps(scene, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(scene, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
