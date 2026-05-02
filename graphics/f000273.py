#!/usr/bin/env python3
# shinmomo_field_vram_analyzer_20260501.py
# 新桃太郎伝説 フィールド移動時 VRAM dump 解析補助
#
# 入力:
#   vram.bin 64KiB
# 出力:
#   - VRAM 1KB region summary
#   - 0x0000..0x7FFF の 16 screen tilemap decode
#   - char_base=0x8000 / 4bpp 前提の field map preview
#   - tile usage / 2x2 metatile pattern usage
#
# 使い方:
#   python shinmomo_field_vram_analyzer_20260501.py --vram vram.bin --out out_field
#
from __future__ import annotations

import argparse
import hashlib
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw


def decode_2bpp_tile(buf: bytes) -> np.ndarray:
    pix = np.zeros((8, 8), dtype=np.uint8)
    for y in range(8):
        p0 = buf[y * 2] if y * 2 < len(buf) else 0
        p1 = buf[y * 2 + 1] if y * 2 + 1 < len(buf) else 0
        for x in range(8):
            bit = 7 - x
            pix[y, x] = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1)
    return pix


def decode_4bpp_tile(buf: bytes) -> np.ndarray:
    pix = np.zeros((8, 8), dtype=np.uint8)
    for y in range(8):
        p0 = buf[y * 2] if y * 2 < len(buf) else 0
        p1 = buf[y * 2 + 1] if y * 2 + 1 < len(buf) else 0
        p2 = buf[16 + y * 2] if 16 + y * 2 < len(buf) else 0
        p3 = buf[16 + y * 2 + 1] if 16 + y * 2 + 1 < len(buf) else 0
        for x in range(8):
            bit = 7 - x
            pix[y, x] = (
                ((p0 >> bit) & 1)
                | (((p1 >> bit) & 1) << 1)
                | (((p2 >> bit) & 1) << 2)
                | (((p3 >> bit) & 1) << 3)
            )
    return pix


def decode_tile(vram: bytes, char_base: int, tile_index: int, bpp: int) -> np.ndarray:
    tile_size = 32 if bpp == 4 else 16
    off = char_base + tile_index * tile_size
    if off < 0 or off + tile_size > len(vram):
        return np.zeros((8, 8), dtype=np.uint8)
    raw = vram[off : off + tile_size]
    return decode_4bpp_tile(raw) if bpp == 4 else decode_2bpp_tile(raw)


def tile_sheet(vram: bytes, bpp: int, start: int, end: int, cols: int = 32, scale: int = 2) -> Image.Image:
    tile_size = 32 if bpp == 4 else 16
    n = max(0, (end - start) // tile_size)
    rows = math.ceil(n / cols) if n else 1
    img = np.zeros((rows * 8, cols * 8), dtype=np.uint8)
    for i in range(n):
        off = start + i * tile_size
        pix = decode_4bpp_tile(vram[off : off + 32]) if bpp == 4 else decode_2bpp_tile(vram[off : off + 16])
        r, c = divmod(i, cols)
        img[r * 8 : r * 8 + 8, c * 8 : c * 8 + 8] = pix
    pal = np.array([i * 17 for i in range(16)], dtype=np.uint8) if bpp == 4 else np.array([0, 85, 170, 255], dtype=np.uint8)
    im = Image.fromarray(pal[img], "L")
    return im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST) if scale != 1 else im


def render_snes_tilemap(
    vram: bytes,
    map_base: int,
    char_base: int,
    bpp: int,
    screen_w: int,
    screen_h: int,
    scale: int = 1,
) -> tuple[Image.Image, np.ndarray]:
    width = 32 * screen_w
    height = 32 * screen_h
    img = np.zeros((height * 8, width * 8), dtype=np.uint8)
    entries = np.zeros((height, width), dtype=np.uint16)

    for y in range(height):
        for x in range(width):
            sx, sy = x // 32, y // 32
            ix, iy = x % 32, y % 32
            screen_index = sy * screen_w + sx
            off = map_base + screen_index * 0x800 + (iy * 32 + ix) * 2
            if off + 2 > len(vram):
                continue
            e = vram[off] | (vram[off + 1] << 8)
            entries[y, x] = e

            tile = e & 0x03FF
            hflip = (e >> 10) & 1
            vflip = (e >> 11) & 1
            pal = (e >> 12) & 7
            pix = decode_tile(vram, char_base, tile, bpp).copy()
            if hflip:
                pix = np.fliplr(pix)
            if vflip:
                pix = np.flipud(pix)

            # CGRAMなしでも層を見やすくするため、palette番号を濃淡に足す
            pix = np.where(pix == 0, 0, pix + pal * (16 if bpp == 4 else 4))
            img[y * 8 : y * 8 + 8, x * 8 : x * 8 + 8] = pix

    maxv = int(img.max()) if int(img.max()) > 0 else 1
    im = Image.fromarray((img / maxv * 255).astype(np.uint8), "L")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
    return im, entries


def summarize_regions(vram: bytes) -> pd.DataFrame:
    arr = np.frombuffer(vram, dtype=np.uint8)
    rows = []
    for start in range(0, 0x10000, 0x400):
        chunk = arr[start : start + 0x400]
        hist = np.bincount(chunk, minlength=256)
        probs = hist[hist > 0] / len(chunk)
        entropy = float(-(probs * np.log2(probs)).sum())
        words = np.frombuffer(chunk.tobytes(), dtype="<u2")
        tile = words & 0x03FF
        rows.append(
            {
                "start": f"0x{start:04X}",
                "end": f"0x{start+0x3FF:04X}",
                "nonzero_bytes": int(np.count_nonzero(chunk)),
                "zero_pct": float((len(chunk) - np.count_nonzero(chunk)) / len(chunk) * 100),
                "unique_byte_values": int(len(set(chunk.tolist()))),
                "entropy": entropy,
                "zero_words": int(np.sum(words == 0)),
                "tile_index_lt512_words": int(np.sum(tile < 512)),
            }
        )
    return pd.DataFrame(rows)


def make_16screen_montage(vram: bytes, out: Path) -> None:
    cell = 128
    mont = Image.new("L", (4 * cell, 4 * (cell + 16)), 0)
    draw = ImageDraw.Draw(mont)
    for idx, mb in enumerate(range(0, 0x8000, 0x800)):
        im, _ = render_snes_tilemap(vram, mb, 0x8000, 4, 1, 1, scale=1)
        im2 = im.resize((cell, cell), Image.Resampling.NEAREST)
        x = (idx % 4) * cell
        y = (idx // 4) * (cell + 16) + 16
        mont.paste(im2, (x, y))
        draw.text((x + 3, y - 14), f"{mb:04X}", fill=255)
    mont.save(out / "field_tilemap_16_screens_map0000_to_7FFF_char8000_4bpp.png")


def extract_tilemaps(vram: bytes, out: Path) -> None:
    rows = []
    usage = Counter()
    entries_counter = Counter()

    for screen_idx, mb in enumerate(range(0, 0x8000, 0x800)):
        sx, sy = screen_idx % 4, screen_idx // 4
        for y in range(32):
            for x in range(32):
                off = mb + (y * 32 + x) * 2
                e = vram[off] | (vram[off + 1] << 8)
                tile = e & 0x03FF
                pal = (e >> 12) & 7
                h = (e >> 10) & 1
                vf = (e >> 11) & 1
                pr = (e >> 15) & 1
                usage[(tile, pal, h, vf, pr)] += 1
                entries_counter[e] += 1
                rows.append(
                    {
                        "screen_index": screen_idx,
                        "screen_vram_base": f"0x{mb:04X}",
                        "screen_x": sx,
                        "screen_y": sy,
                        "x": x,
                        "y": y,
                        "global_x_assuming_4x4": sx * 32 + x,
                        "global_y_assuming_4x4": sy * 32 + y,
                        "entry_hex": f"0x{e:04X}",
                        "tile": tile,
                        "tile_hex": f"0x{tile:03X}",
                        "tile_vram_offset_if_charbase_8000_4bpp": f"0x{0x8000 + tile * 32:04X}" if 0x8000 + tile * 32 < 0x10000 else "",
                        "palette": pal,
                        "hflip": h,
                        "vflip": vf,
                        "priority": pr,
                    }
                )
    pd.DataFrame(rows).to_csv(out / "field_vram_0000_7fff_tilemap_entries_decoded.csv", index=False)

    usage_rows = []
    for (tile, pal, h, vf, pr), cnt in usage.most_common():
        off = 0x8000 + tile * 32
        usage_rows.append(
            {
                "tile": tile,
                "tile_hex": f"0x{tile:03X}",
                "count": cnt,
                "palette": pal,
                "hflip": h,
                "vflip": vf,
                "priority": pr,
                "vram_offset_if_charbase_8000_4bpp": f"0x{off:04X}" if off < 0x10000 else "",
            }
        )
    pd.DataFrame(usage_rows).to_csv(out / "field_tile_usage_charbase8000_4bpp.csv", index=False)

    screen_rows = []
    df = pd.DataFrame(rows)
    for screen_idx, g in df.groupby("screen_index"):
        entries = [int(x, 16) for x in g["entry_hex"]]
        tiles = list(g["tile"])
        pals = list(g["palette"])
        screen_rows.append(
            {
                "screen_index": int(screen_idx),
                "vram_base": f"0x{screen_idx*0x800:04X}",
                "unique_entries": len(set(entries)),
                "unique_tiles": len(set(tiles)),
                "tile_min": min(tiles),
                "tile_max": max(tiles),
                "palette_counts": dict(Counter(pals)),
                "top_entries": ";".join([f"0x{k:04X}:{v}" for k, v in Counter(entries).most_common(10)]),
                "top_tiles": ";".join([f"0x{k:03X}:{v}" for k, v in Counter(tiles).most_common(10)]),
            }
        )
    pd.DataFrame(screen_rows).to_csv(out / "field_tilemap_screen_summary.csv", index=False)


def extract_2x2_metatiles(vram: bytes, out: Path) -> None:
    metas = Counter()
    meta_rows = []
    for screen_idx, mb in enumerate(range(0, 0x8000, 0x800)):
        entries32 = np.frombuffer(vram[mb : mb + 0x800], dtype="<u2").reshape(32, 32)
        for my in range(16):
            for mx in range(16):
                block = entries32[my * 2 : my * 2 + 2, mx * 2 : mx * 2 + 2]
                key = tuple(int(x) for x in block.flatten())
                metas[key] += 1
                meta_rows.append(
                    {
                        "screen_index": screen_idx,
                        "screen_vram_base": f"0x{mb:04X}",
                        "metatile_x": mx,
                        "metatile_y": my,
                        "tl": f"0x{key[0]:04X}",
                        "tr": f"0x{key[1]:04X}",
                        "bl": f"0x{key[2]:04X}",
                        "br": f"0x{key[3]:04X}",
                        "tile_tl": key[0] & 0x03FF,
                        "tile_tr": key[1] & 0x03FF,
                        "tile_bl": key[2] & 0x03FF,
                        "tile_br": key[3] & 0x03FF,
                    }
                )
    pd.DataFrame(meta_rows).to_csv(out / "field_2x2_metatile_occurrences.csv", index=False)

    meta_usage_rows = []
    for i, (key, cnt) in enumerate(metas.most_common()):
        meta_usage_rows.append(
            {
                "pattern_id": i,
                "count": cnt,
                "tl": f"0x{key[0]:04X}",
                "tr": f"0x{key[1]:04X}",
                "bl": f"0x{key[2]:04X}",
                "br": f"0x{key[3]:04X}",
                "tiles": ",".join(f"0x{x & 0x03FF:03X}" for x in key),
                "pals": ",".join(str((x >> 12) & 7) for x in key),
                "hflips": ",".join(str((x >> 10) & 1) for x in key),
                "vflips": ",".join(str((x >> 11) & 1) for x in key),
                "priority": ",".join(str((x >> 15) & 1) for x in key),
            }
        )
    pd.DataFrame(meta_usage_rows).to_csv(out / "field_2x2_metatile_pattern_usage.csv", index=False)

    # visual catalog
    topN = min(128, len(metas))
    cols = 16
    cell = 32
    label_h = 10
    cat = Image.new("L", (cols * cell, math.ceil(topN / cols) * (cell + label_h)), 0)
    draw = ImageDraw.Draw(cat)

    def render_block(key):
        block_img = np.zeros((16, 16), dtype=np.uint8)
        for i, e in enumerate(key):
            y, x = (i // 2) * 8, (i % 2) * 8
            tile = e & 0x03FF
            h = (e >> 10) & 1
            vf = (e >> 11) & 1
            pal = (e >> 12) & 7
            pix = decode_tile(vram, 0x8000, tile, 4).copy()
            if h:
                pix = np.fliplr(pix)
            if vf:
                pix = np.flipud(pix)
            pix = np.where(pix == 0, 0, pix + pal * 16)
            block_img[y : y + 8, x : x + 8] = pix
        return block_img

    for i, (key, cnt) in enumerate(metas.most_common(topN)):
        block = render_block(key)
        im = Image.fromarray((block / (block.max() or 1) * 255).astype(np.uint8), "L").resize((cell, cell), Image.Resampling.NEAREST)
        x = (i % cols) * cell
        y = (i // cols) * (cell + label_h) + label_h
        cat.paste(im, (x, y))
        draw.text((x + 1, y - label_h), f"{i}:{cnt}", fill=255)

    cat.save(out / "field_top_2x2_metatile_patterns.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vram", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    vram = args.vram.read_bytes()
    if len(vram) != 0x10000:
        raise SystemExit(f"vram.bin must be 65536 bytes, got {len(vram)}")

    args.out.mkdir(parents=True, exist_ok=True)

    (args.out / "vram_md5.txt").write_text(hashlib.md5(vram).hexdigest() + "\n", encoding="utf-8")
    summarize_regions(vram).to_csv(args.out / "field_vram_region_summary_1kb.csv", index=False)

    # Core finding: field tilemap appears coherent at map_base=0x0000, char_base=0x8000, bpp=4.
    for name, sw, sh in [("32x32", 1, 1), ("64x32", 2, 1), ("32x64", 1, 2), ("64x64", 2, 2)]:
        im, _ = render_snes_tilemap(vram, 0x0000, 0x8000, 4, sw, sh, scale=1)
        im.save(args.out / f"field_bg_candidate_map0000_char8000_4bpp_{name}.png")
        im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST).save(
            args.out / f"field_bg_candidate_map0000_char8000_4bpp_{name}_2x.png"
        )

    make_16screen_montage(vram, args.out)
    extract_tilemaps(vram, args.out)
    extract_2x2_metatiles(vram, args.out)

    for start, end in [(0x0000, 0x8000), (0x8000, 0xA800), (0xC000, 0xDC00), (0xF000, 0x10000)]:
        tile_sheet(vram, 2, start, end).save(args.out / f"vram_{start:04X}_{end:04X}_2bpp_sheet.png")
        tile_sheet(vram, 4, start, end).save(args.out / f"vram_{start:04X}_{end:04X}_4bpp_sheet.png")

    print(f"Wrote analysis to {args.out}")


if __name__ == "__main__":
    main()
