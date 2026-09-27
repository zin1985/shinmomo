#!/usr/bin/env python3
"""Rank 0x800-byte SNES VRAM pages by tilemap-like structure.

This is for Shinmomo map salvage when the active BizHawk/Snes9x core exposes
VRAM but does not provide readable PPU register mirrors.

SNES BG screen bases are aligned to 0x800 bytes (0x400 words). Each candidate
page is decoded as a 32x32 tilemap of 16-bit entries. Graphics/tile-data pages
can also be interpreted as entries, so this script deliberately scores only
structural evidence:

- repeated 16-bit entries;
- repeated non-overlapping 2x2 metatiles;
- low entropy in palette/flip/priority control bits;
- repeated horizontal/vertical neighbours;
- dominant entry/palette fractions.

The result is a candidate ranking, not proof of BG assignment. A page should be
promoted only after visual/runtime or loader/DMA evidence agrees.

Outputs:
- tilemap_page_ranking.csv
- top_candidates.json
- page_XXXX_entries.csv for top candidates
- page_XXXX_tile_ids.pgm for top candidates (structure-only grayscale preview)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path


PAGE_SIZE = 0x800
CELLS = 32 * 32


def entropy(counts: Counter[int], total: int) -> float:
    if total <= 0:
        return 0.0
    h = 0.0
    for n in counts.values():
        if n:
            p = n / total
            h -= p * math.log2(p)
    return h


def decode_page(vram: bytes, base: int) -> list[int]:
    return [
        vram[base + i * 2] | (vram[base + i * 2 + 1] << 8)
        for i in range(CELLS)
    ]


def page_metrics(entries: list[int]) -> dict:
    ec = Counter(entries)
    tiles = [e & 0x03FF for e in entries]
    palettes = [(e >> 10) & 0x07 for e in entries]
    priority = [(e >> 13) & 1 for e in entries]
    hflip = [(e >> 14) & 1 for e in entries]
    vflip = [(e >> 15) & 1 for e in entries]

    tc = Counter(tiles)
    pc = Counter(palettes)
    ctrl = Counter((e >> 10) & 0x3F for e in entries)

    same_r = 0
    same_d = 0
    pairs_r = 0
    pairs_d = 0
    for y in range(32):
        for x in range(32):
            i = y * 32 + x
            if x + 1 < 32:
                pairs_r += 1
                same_r += entries[i] == entries[i + 1]
            if y + 1 < 32:
                pairs_d += 1
                same_d += entries[i] == entries[i + 32]

    mts = []
    for my in range(16):
        for mx in range(16):
            x, y = mx * 2, my * 2
            i = y * 32 + x
            mts.append((entries[i], entries[i + 1], entries[i + 32], entries[i + 33]))
    mtc = Counter(mts)

    unique_entries = len(ec)
    unique_tiles = len(tc)
    unique_mts = len(mtc)
    entry_repeat = 1.0 - unique_entries / CELLS
    tile_repeat = 1.0 - unique_tiles / CELLS
    metatile_repeat = 1.0 - unique_mts / 256
    neighbor_repeat = ((same_r / pairs_r) + (same_d / pairs_d)) / 2
    dominant_entry = ec.most_common(1)[0][1] / CELLS
    dominant_palette = pc.most_common(1)[0][1] / CELLS
    palette_entropy = entropy(pc, CELLS) / 3.0  # max 3 bits for 8 palettes
    ctrl_entropy = entropy(ctrl, CELLS) / 6.0   # max 6 bits

    # Tilemaps usually reuse entries/metatiles and use a comparatively small
    # subset of palette/flip/priority control states. Do not reward all-zero
    # pages excessively; they are technically structured but not useful maps.
    zero_ratio = ec.get(0, 0) / CELLS
    blank_penalty = max(0.0, (zero_ratio - 0.85) / 0.15)
    low_ctrl_entropy = 1.0 - min(1.0, ctrl_entropy)
    low_palette_entropy = 1.0 - min(1.0, palette_entropy)
    priority_one = sum(priority) / CELLS
    low_priority = 1.0 - priority_one

    # Useful map pages are neither constant fills nor near-random graphics.
    # Reward a broad "working diversity" band and strongly suppress pages with
    # fewer than 8 distinct entries.
    if unique_entries < 4:
        diversity_quality = 0.0
    elif unique_entries < 8:
        diversity_quality = (unique_entries - 4) / 4
    elif unique_entries <= 320:
        diversity_quality = 1.0
    else:
        diversity_quality = max(0.0, 1.0 - (unique_entries - 320) / 704)

    constant_penalty = max(0.0, (8 - unique_entries) / 8)

    score = (
        0.20 * entry_repeat
        + 0.18 * metatile_repeat
        + 0.08 * tile_repeat
        + 0.09 * neighbor_repeat
        + 0.08 * dominant_palette
        + 0.08 * low_ctrl_entropy
        + 0.04 * low_palette_entropy
        + 0.13 * low_priority
        + 0.12 * diversity_quality
        - 0.38 * blank_penalty
        - 0.45 * constant_penalty
    )

    return {
        "score": score,
        "unique_entries": unique_entries,
        "unique_tiles": unique_tiles,
        "unique_metatiles_2x2": unique_mts,
        "entry_repeat_ratio": entry_repeat,
        "tile_repeat_ratio": tile_repeat,
        "metatile_repeat_ratio": metatile_repeat,
        "neighbor_repeat_ratio": neighbor_repeat,
        "dominant_entry_ratio": dominant_entry,
        "dominant_palette_ratio": dominant_palette,
        "palette_entropy_norm": palette_entropy,
        "control_entropy_norm": ctrl_entropy,
        "zero_entry_ratio": zero_ratio,
        "priority_1_ratio": priority_one,
        "diversity_quality": diversity_quality,
        "constant_penalty": constant_penalty,
        "hflip_1_ratio": sum(hflip) / CELLS,
        "vflip_1_ratio": sum(vflip) / CELLS,
        "palette_count": len(pc),
        "control_state_count": len(ctrl),
        "most_common_entry": ec.most_common(1)[0][0],
        "most_common_tile": tc.most_common(1)[0][0],
    }


def write_page_csv(path: Path, base: int, entries: list[int]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "page_base", "cell", "tx", "ty", "vram_addr", "entry_hex",
            "tile", "palette", "priority", "hflip", "vflip"
        ])
        for cell, e in enumerate(entries):
            x, y = cell % 32, cell // 32
            w.writerow([
                f"0x{base:04X}", cell, x, y, f"0x{base + cell*2:04X}",
                f"0x{e:04X}", e & 0x03FF, (e >> 10) & 7,
                (e >> 13) & 1, (e >> 14) & 1, (e >> 15) & 1,
            ])


def write_pgm(path: Path, entries: list[int]) -> None:
    # Structure preview only: map tile number to 0..255. Each entry becomes
    # an 8x8 block to make the 32x32 page readable.
    width = height = 32 * 8
    pix = bytearray(width * height)
    for cell, e in enumerate(entries):
        tx, ty = cell % 32, cell // 32
        v = ((e & 0x03FF) * 255) // 1023
        for py in range(8):
            row = (ty * 8 + py) * width
            for px in range(8):
                pix[row + tx * 8 + px] = v
    path.write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + bytes(pix))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vram", type=Path)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    vram = args.vram.read_bytes()
    if len(vram) != 0x10000:
        raise SystemExit(f"expected 65536-byte VRAM dump, got {len(vram)}")

    out = args.out_dir or args.vram.parent / "tilemap_rank"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    pages: dict[int, list[int]] = {}
    for base in range(0, 0x10000, PAGE_SIZE):
        entries = decode_page(vram, base)
        pages[base] = entries
        m = page_metrics(entries)
        rows.append({
            "page_base": f"0x{base:04X}",
            **{k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in m.items()},
            "most_common_entry": f"0x{m['most_common_entry']:04X}",
            "most_common_tile": f"0x{m['most_common_tile']:03X}",
        })

    rows.sort(key=lambda r: float(r["score"]), reverse=True)

    ranking_path = out / "tilemap_page_ranking.csv"
    with ranking_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    top = rows[: max(1, args.top)]
    for rank, row in enumerate(top, 1):
        base = int(row["page_base"], 16)
        stem = f"rank{rank:02d}_page_{base:04X}"
        write_page_csv(out / f"{stem}_entries.csv", base, pages[base])
        write_pgm(out / f"{stem}_tile_ids.pgm", pages[base])

    summary = {
        "schema_version": 1,
        "source_vram": str(args.vram),
        "candidate_count": len(rows),
        "ranking_method": "tilemap structural reuse heuristic; candidate only, not BG proof",
        "top": [
            {
                "rank": i,
                "page_base": r["page_base"],
                "score": float(r["score"]),
                "unique_entries": int(r["unique_entries"]),
                "unique_tiles": int(r["unique_tiles"]),
                "unique_metatiles_2x2": int(r["unique_metatiles_2x2"]),
                "metatile_repeat_ratio": float(r["metatile_repeat_ratio"]),
                "dominant_palette_ratio": float(r["dominant_palette_ratio"]),
                "zero_entry_ratio": float(r["zero_entry_ratio"]),
            }
            for i, r in enumerate(top, 1)
        ],
    }
    (out / "top_candidates.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
