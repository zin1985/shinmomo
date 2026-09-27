#!/usr/bin/env python3
"""Infer SNES BG rendering parameters from VRAM + screenshot structure.

Use when BizHawk exposes VRAM but the active SNES core does not expose readable
BGMODE/BGnSC/BGnNBA mirrors.

For each candidate 0x800-byte tilemap page, this tool brute-forces:
- bpp: 2 / 4 / 8
- character base: 0x0000..0xF000 in 0x1000 steps
- tile-aligned scroll X/Y

It compares tile-level structural features against the runtime screenshot:
- local edge density
- local variance / visual complexity

The output is an inference ranking, not canonical proof. Promote parameters only
after repeated captures or ROM loader/DMA evidence agree.

Requires Pillow and NumPy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def parse_int(s: str) -> int:
    return int(s, 0)


def decode_tile(vram: bytes, base: int, tile: int, bpp: int) -> np.ndarray:
    size = {2: 16, 4: 32, 8: 64}[bpp]
    addr = (base + tile * size) & 0xFFFF
    out = np.zeros((8, 8), dtype=np.uint8)

    def rb(off: int) -> int:
        return vram[(addr + off) & 0xFFFF]

    for y in range(8):
        p0 = rb(y * 2)
        p1 = rb(y * 2 + 1)
        p2 = rb(16 + y * 2) if bpp >= 4 else 0
        p3 = rb(16 + y * 2 + 1) if bpp >= 4 else 0
        p4 = rb(32 + y * 2) if bpp >= 8 else 0
        p5 = rb(32 + y * 2 + 1) if bpp >= 8 else 0
        p6 = rb(48 + y * 2) if bpp >= 8 else 0
        p7 = rb(48 + y * 2 + 1) if bpp >= 8 else 0
        for x in range(8):
            bit = 7 - x
            out[y, x] = (
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
                | (((p4 >> bit) & 1) << 4)
                | (((p5 >> bit) & 1) << 5)
                | (((p6 >> bit) & 1) << 6)
                | (((p7 >> bit) & 1) << 7)
            )
    return out


def tile_features(tile: np.ndarray) -> tuple[float, float]:
    # Palette-independent structure. Flat tiles have low complexity.
    uniq = len(np.unique(tile))
    maxc = max(2, int(tile.max()) + 1)
    complexity = min(1.0, (uniq - 1) / min(15.0, maxc - 1))
    h = (tile[:, 1:] != tile[:, :-1]).mean()
    v = (tile[1:, :] != tile[:-1, :]).mean()
    edge = float((h + v) / 2)
    return complexity, edge


def screenshot_features(path: Path) -> np.ndarray:
    im = Image.open(path).convert("L")
    # SNES game image is normally 256x224. If a capture differs, resize to
    # preserve the coarse 32x28 tile feature comparison.
    if im.size != (256, 224):
        im = im.resize((256, 224), Image.Resampling.BILINEAR)
    a = np.asarray(im, dtype=np.float32)
    feat = np.zeros((28, 32, 2), dtype=np.float32)
    for ty in range(28):
        for tx in range(32):
            t = a[ty*8:(ty+1)*8, tx*8:(tx+1)*8]
            std = float(t.std() / 64.0)
            std = min(1.0, std)
            h = np.abs(t[:, 1:] - t[:, :-1]).mean() / 64.0
            v = np.abs(t[1:, :] - t[:-1, :]).mean() / 64.0
            edge = min(1.0, float((h + v) / 2))
            feat[ty, tx] = (std, edge)
    return feat


def normalized_similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Correlate both channels after per-channel normalization.
    vals = []
    for ch in range(a.shape[2]):
        x = a[:, :, ch].ravel().astype(np.float64)
        y = b[:, :, ch].ravel().astype(np.float64)
        xs, ys = x.std(), y.std()
        if xs < 1e-9 or ys < 1e-9:
            vals.append(0.0)
            continue
        x = (x - x.mean()) / xs
        y = (y - y.mean()) / ys
        vals.append(float(np.mean(x * y)))
    return float(sum(vals) / len(vals))


def decode_entries(vram: bytes, page: int) -> np.ndarray:
    e = np.zeros((32, 32), dtype=np.uint16)
    for i in range(1024):
        off = page + i * 2
        e[i // 32, i % 32] = vram[off] | (vram[off + 1] << 8)
    return e


def candidate_feature_grid(vram: bytes, entries: np.ndarray, char_base: int, bpp: int) -> np.ndarray:
    cache: dict[tuple[int, int, int], tuple[float, float]] = {}
    out = np.zeros((32, 32, 2), dtype=np.float32)
    for y in range(32):
        for x in range(32):
            e = int(entries[y, x])
            tile = e & 0x03FF
            hf = (e >> 14) & 1
            vf = (e >> 15) & 1
            key = (tile, hf, vf)
            if key not in cache:
                pix = decode_tile(vram, char_base, tile, bpp)
                if hf:
                    pix = pix[:, ::-1]
                if vf:
                    pix = pix[::-1, :]
                cache[key] = tile_features(pix)
            out[y, x] = cache[key]
    return out


def visible_grid(grid: np.ndarray, sx: int, sy: int) -> np.ndarray:
    # 32x28 viewport, wrapping inside a 32x32 tilemap page.
    ys = [(sy + i) % 32 for i in range(28)]
    xs = [(sx + i) % 32 for i in range(32)]
    return grid[np.ix_(ys, xs)]


def render_index_preview(
    vram: bytes,
    entries: np.ndarray,
    char_base: int,
    bpp: int,
    sx: int,
    sy: int,
    path: Path,
) -> None:
    """Render palette-independent color indices for visual validation."""
    max_color = (1 << bpp) - 1
    out = np.zeros((224, 256), dtype=np.uint8)
    cache: dict[tuple[int, int, int], np.ndarray] = {}
    for vy in range(28):
        my = (sy + vy) % 32
        for vx in range(32):
            mx = (sx + vx) % 32
            e = int(entries[my, mx])
            tile = e & 0x03FF
            hf = (e >> 14) & 1
            vf = (e >> 15) & 1
            key = (tile, hf, vf)
            if key not in cache:
                pix = decode_tile(vram, char_base, tile, bpp)
                if hf:
                    pix = pix[:, ::-1]
                if vf:
                    pix = pix[::-1, :]
                cache[key] = pix
            pix = cache[key]
            scaled = (pix.astype(np.uint16) * 255 // max(1, max_color)).astype(np.uint8)
            out[vy*8:(vy+1)*8, vx*8:(vx+1)*8] = scaled
    Image.fromarray(out, mode="L").save(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vram", type=Path)
    ap.add_argument("screenshot", type=Path)
    ap.add_argument("--pages", nargs="+", required=True, type=parse_int)
    ap.add_argument("--bpp", nargs="+", default=[2, 4, 8], type=int)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    vram = args.vram.read_bytes()
    if len(vram) != 0x10000:
        raise SystemExit(f"expected 65536-byte VRAM dump, got {len(vram)}")

    target = screenshot_features(args.screenshot)
    results = []

    for page in args.pages:
        entries = decode_entries(vram, page)
        for bpp in args.bpp:
            for char_base in range(0, 0x10000, 0x1000):
                grid = candidate_feature_grid(vram, entries, char_base, bpp)
                best = (-999.0, 0, 0)
                for sy in range(32):
                    # horizontal viewport is exactly 32 tiles, so sx only
                    # reorders/wraps columns; still search all values.
                    for sx in range(32):
                        sim = normalized_similarity(target, visible_grid(grid, sx, sy))
                        if sim > best[0]:
                            best = (sim, sx, sy)
                results.append({
                    "page_base": f"0x{page:04X}",
                    "bpp": bpp,
                    "char_base": f"0x{char_base:04X}",
                    "similarity": best[0],
                    "scroll_tile_x": best[1],
                    "scroll_tile_y": best[2],
                })

    results.sort(key=lambda r: r["similarity"], reverse=True)
    payload = {
        "schema_version": 1,
        "vram": str(args.vram),
        "screenshot": str(args.screenshot),
        "method": "tile-level structural correlation; inference only",
        "top": results[:args.top],
    }
    out = args.out or args.vram.parent / "bg_render_inference.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preview_dir = out.parent / (out.stem + "_previews")
    preview_dir.mkdir(parents=True, exist_ok=True)
    page_cache: dict[int, np.ndarray] = {}
    for rank, row in enumerate(results[: min(args.top, 10)], 1):
        page = int(row["page_base"], 16)
        if page not in page_cache:
            page_cache[page] = decode_entries(vram, page)
        char_base = int(row["char_base"], 16)
        render_index_preview(
            vram,
            page_cache[page],
            char_base,
            int(row["bpp"]),
            int(row["scroll_tile_x"]),
            int(row["scroll_tile_y"]),
            preview_dir / (
                f"rank{rank:02d}_page_{page:04X}_"
                f"{row['bpp']}bpp_char_{char_base:04X}_"
                f"sx{row['scroll_tile_x']:02d}_sy{row['scroll_tile_y']:02d}.png"
            ),
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
