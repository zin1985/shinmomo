#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shinmomo_graphics_probe_v1.py

新桃太郎伝説 ROM グラフィック調査用プローブ。
1) ROM全域の SNES 2bpp/4bpp タイルシートPNG出力
2) フォント候補、顔/人物候補、マップチップ候補の簡易スコア抽出
3) DA:3800 既存decoded CSVがあれば、stream別の小資材ビューを出力

注意:
- 生ROMの未圧縮タイルを可視化するための探索器です。
- 圧縮済み素材は生表示だと崩れます。
- 正しいゲーム画面再現には、実行時VRAM/CGRAM/tilemap dumpが必要です。
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import statistics
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont


def load_rom(path: Path) -> bytes:
    data = path.read_bytes()
    # 2MB + 512 header case
    if len(data) % 0x8000 == 0x200:
        data = data[0x200:]
    return data


def pc_to_lorom(pc: int) -> str:
    bank = 0x80 + (pc // 0x8000)
    addr = 0x8000 + (pc % 0x8000)
    return f"{bank:02X}:{addr:04X}"


def palette_gray(n: int = 16) -> List[int]:
    pal: List[int] = []
    for i in range(n):
        v = int(i * 255 / max(1, n - 1))
        pal.extend([v, v, v])
    pal.extend([0, 0, 0] * (256 - n))
    return pal


def decode_tile_2bpp(tile: bytes) -> List[List[int]]:
    px = [[0] * 8 for _ in range(8)]
    if len(tile) < 16:
        tile = tile + b"\x00" * (16 - len(tile))
    for y in range(8):
        p0 = tile[y * 2]
        p1 = tile[y * 2 + 1]
        for x in range(8):
            b = 7 - x
            px[y][x] = ((p0 >> b) & 1) | (((p1 >> b) & 1) << 1)
    return px


def decode_tile_4bpp(tile: bytes) -> List[List[int]]:
    px = [[0] * 8 for _ in range(8)]
    if len(tile) < 32:
        tile = tile + b"\x00" * (32 - len(tile))
    for y in range(8):
        p0 = tile[y * 2]
        p1 = tile[y * 2 + 1]
        p2 = tile[16 + y * 2]
        p3 = tile[16 + y * 2 + 1]
        for x in range(8):
            b = 7 - x
            px[y][x] = ((p0 >> b) & 1) | (((p1 >> b) & 1) << 1) | (((p2 >> b) & 1) << 2) | (((p3 >> b) & 1) << 3)
    return px


def tile_entropy(vals: List[int]) -> float:
    if not vals:
        return 0.0
    counts: Dict[int, int] = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    total = len(vals)
    ent = 0.0
    for c in counts.values():
        p = c / total
        ent -= p * math.log2(p)
    return ent


def tile_stats(px: List[List[int]]) -> Tuple[float, int, float, bool, float]:
    vals = [v for row in px for v in row]
    nonzero = sum(1 for v in vals if v != 0) / 64.0
    uniq = len(set(vals))
    ent = tile_entropy(vals)
    blank = uniq == 1
    # outer margin emptiness helps find font-like 8x8 glyphs
    margin = []
    margin.extend(px[0])
    margin.extend(px[-1])
    margin.extend(row[0] for row in px)
    margin.extend(row[-1] for row in px)
    margin_zero = sum(1 for v in margin if v == 0) / len(margin)
    return nonzero, uniq, ent, blank, margin_zero


def render_sheet(data: bytes, bpp: int, tiles_per_row: int = 32, max_tiles: int | None = None, scale: int = 1) -> Image.Image:
    tile_size = 16 if bpp == 2 else 32
    decoder = decode_tile_2bpp if bpp == 2 else decode_tile_4bpp
    n = len(data) // tile_size
    if max_tiles is not None:
        n = min(n, max_tiles)
    rows = max(1, math.ceil(n / tiles_per_row))
    im = Image.new("P", (tiles_per_row * 8, rows * 8), 0)
    im.putpalette(palette_gray(4 if bpp == 2 else 16))
    for t in range(n):
        px = decoder(data[t * tile_size:(t + 1) * tile_size])
        ox = (t % tiles_per_row) * 8
        oy = (t // tiles_per_row) * 8
        for y in range(8):
            for x in range(8):
                im.putpixel((ox + x, oy + y), px[y][x])
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)
    return im


@dataclass
class WindowScore:
    offset: int
    snes: str
    bpp: int
    chunk_size: int
    visual_score: float
    font_score: float
    face_score: float
    map_score: float
    nonblank_ratio: float
    avg_nonzero: float
    avg_entropy: float
    avg_unique: float
    duplicate_ratio: float


def score_window(data: bytes, offset: int, bpp: int, chunk_size: int = 0x1000) -> WindowScore:
    tile_size = 16 if bpp == 2 else 32
    decoder = decode_tile_2bpp if bpp == 2 else decode_tile_4bpp
    chunk = data[offset:offset + chunk_size]
    n = len(chunk) // tile_size
    stats = []
    raw_tiles = []
    for i in range(n):
        tile = chunk[i * tile_size:(i + 1) * tile_size]
        raw_tiles.append(tile)
        px = decoder(tile)
        stats.append(tile_stats(px))
    if not stats:
        return WindowScore(offset, pc_to_lorom(offset), bpp, chunk_size, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    nonzero = [s[0] for s in stats]
    uniq = [s[1] for s in stats]
    ent = [s[2] for s in stats]
    blank = [s[3] for s in stats]
    margin = [s[4] for s in stats]
    nonblank_ratio = sum(1 for b in blank if not b) / len(blank)
    avg_nonzero = statistics.mean(nonzero)
    avg_entropy = statistics.mean(ent)
    avg_unique = statistics.mean(uniq)
    duplicate_ratio = 1.0 - (len(set(raw_tiles)) / max(1, len(raw_tiles)))

    # Generic visualness: not blank, not full-random, with moderate entropy.
    visual_tiles = sum(1 for nz, u, e, bl, m in stats if (not bl and 0.03 <= nz <= 0.92 and 0.10 <= e <= (1.95 if bpp == 2 else 3.60)))
    visual_score = 100.0 * visual_tiles / len(stats)

    # Font-like: sparse-ish, margin-heavy, low color count, many simple glyphs.
    font_tiles = sum(1 for nz, u, e, bl, m in stats if (not bl and 0.04 <= nz <= 0.55 and m >= 0.45 and u <= (4 if bpp == 2 else 6) and 0.15 <= e <= 2.2))
    font_score = 100.0 * font_tiles / len(stats)
    if bpp == 2:
        font_score *= 1.25

    # Face/person-like: dense 4bpp art chunks, higher color variation, low blanking.
    face_tiles = sum(1 for nz, u, e, bl, m in stats if (not bl and 0.18 <= nz <= 0.92 and u >= (4 if bpp == 4 else 3) and 0.8 <= e <= (3.8 if bpp == 4 else 2.0)))
    face_score = 100.0 * face_tiles / len(stats)
    if bpp == 4:
        face_score *= 1.15

    # Mapchip-like: lots of nonblank repeating-ish material, but not random.
    map_score = visual_score * (0.65 + min(0.35, duplicate_ratio))
    if nonblank_ratio > 0.50:
        map_score *= 1.10
    if bpp == 4:
        map_score *= 1.05

    return WindowScore(offset, pc_to_lorom(offset), bpp, chunk_size, visual_score, font_score, face_score, map_score,
                       nonblank_ratio, avg_nonzero, avg_entropy, avg_unique, duplicate_ratio)


def dump_full_sheets(data: bytes, out_dir: Path, bpp: int, chunk_size: int = 0x4000) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for off in range(0, len(data), chunk_size):
        im = render_sheet(data[off:off + chunk_size], bpp=bpp, tiles_per_row=32, scale=1)
        path = out_dir / f"raw{bpp}bpp_pc{off:06X}_{pc_to_lorom(off).replace(':','_')}.png"
        im.save(path)
        paths.append(path)
    return paths


def write_scores_csv(scores: List[WindowScore], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["offset", "snes", "bpp", "chunk_size", "visual_score", "font_score", "face_score", "map_score", "nonblank_ratio", "avg_nonzero", "avg_entropy", "avg_unique", "duplicate_ratio"])
        for s in scores:
            w.writerow([f"0x{s.offset:06X}", s.snes, s.bpp, f"0x{s.chunk_size:X}", f"{s.visual_score:.2f}", f"{s.font_score:.2f}", f"{s.face_score:.2f}", f"{s.map_score:.2f}", f"{s.nonblank_ratio:.3f}", f"{s.avg_nonzero:.3f}", f"{s.avg_entropy:.3f}", f"{s.avg_unique:.3f}", f"{s.duplicate_ratio:.3f}"])


def annotate(img: Image.Image, title: str) -> Image.Image:
    rgb = img.convert("RGB")
    top = 18
    out = Image.new("RGB", (rgb.width, rgb.height + top), (255, 255, 255))
    out.paste(rgb, (0, top))
    d = ImageDraw.Draw(out)
    d.text((2, 2), title, fill=(0, 0, 0))
    return out


def contact_sheet(items: List[Tuple[str, Image.Image]], cols: int = 4, bg=(255, 255, 255)) -> Image.Image:
    if not items:
        return Image.new("RGB", (320, 32), bg)
    w = max(im.width for _, im in items)
    h = max(im.height for _, im in items)
    rows = math.ceil(len(items) / cols)
    out = Image.new("RGB", (w * cols, h * rows), bg)
    for i, (title, im) in enumerate(items):
        out.paste(annotate(im, title), ((i % cols) * w, (i // cols) * h))
    return out


def dump_top_candidates(data: bytes, scores: List[WindowScore], out_dir: Path, category: str, bpp_filter: int | None, key: str, top_n: int = 32) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    filtered = [s for s in scores if bpp_filter is None or s.bpp == bpp_filter]
    filtered.sort(key=lambda s: getattr(s, key), reverse=True)
    selected = filtered[:top_n]
    paths = []
    thumbs: List[Tuple[str, Image.Image]] = []
    for rank, s in enumerate(selected, 1):
        im = render_sheet(data[s.offset:s.offset + s.chunk_size], bpp=s.bpp, tiles_per_row=16, scale=2)
        label = f"#{rank:02d} pc{s.offset:06X} {s.snes} {s.bpp}b {key}={getattr(s,key):.1f}"
        path = out_dir / f"{category}_{rank:02d}_pc{s.offset:06X}_{s.snes.replace(':','_')}_{s.bpp}bpp.png"
        annotate(im, label).save(path)
        paths.append(path)
        if len(thumbs) < 16:
            thumbs.append((label, im))
    if thumbs:
        cs = contact_sheet(thumbs, cols=4)
        cs_path = out_dir / f"{category}_contact_sheet_top16.png"
        cs.save(cs_path)
        paths.append(cs_path)
    return paths


def render_known_regions(data: bytes, out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    known = [
        (0x026A60, 0x026C3F, "known_26A60_26C3F_UI_display_definition_candidate"),
        (0x04EA30, 0x04EC80, "known_4EA30_4EC80_pointer_dma_related_candidate"),
        (0x1A3800, 0x1A70A6, "known_DA3800_asset_pointer_stream_area_part1"),
    ]
    paths = []
    for start, end, name in known:
        chunk = data[start:min(end + 1, len(data))]
        for bpp in (2, 4):
            im = render_sheet(chunk, bpp=bpp, tiles_per_row=16, scale=2)
            label = f"{name} pc{start:06X}-{end:06X} {pc_to_lorom(start)} {bpp}bpp raw"
            path = out_dir / f"{name}_{bpp}bpp.png"
            annotate(im, label).save(path)
            paths.append(path)
    return paths


def render_da3800_decoded(csv_path: Path, out_dir: Path) -> List[Path]:
    if not csv_path.exists():
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with csv_path.open("r", encoding="utf-utf-8-sig" if False else "utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        return []
    # Render each record as 4 panels of 8x16 1bpp-like data: seg0, seg1 unpack nibbles padded, seg2, seg3 unpack.
    by_stream: Dict[int, List[dict]] = {}
    for row in rows:
        try:
            sid = int(row.get("stream_id", "0"))
        except Exception:
            sid = 0
        by_stream.setdefault(sid, []).append(row)
    paths = []
    max_streams = 22
    for sid in sorted(by_stream)[:max_streams]:
        recs = by_stream[sid]
        # one record = 16x16 composite from seg0 and seg2 (outline/fill style)
        cols = 16
        cell = 16
        rows_n = math.ceil(len(recs) / cols)
        im = Image.new("P", (cols * cell, rows_n * cell), 0)
        pal = [255,255,255, 0,0,0, 120,120,120, 200,200,200] + [0,0,0]*(256-4)
        im.putpalette(pal)
        for idx, r in enumerate(recs):
            x0 = (idx % cols) * cell
            y0 = (idx // cols) * cell
            seg0 = bytes.fromhex(r.get("seg0_bytes_hex", "")[:32].ljust(32, "0"))
            seg2 = bytes.fromhex(r.get("seg2_bytes_hex", "")[:32].ljust(32, "0"))
            # 8x16 left/right panels: left=seg0, right=seg2, combined in 16x16.
            for y in range(16):
                b0 = seg0[y] if y < len(seg0) else 0
                b2 = seg2[y] if y < len(seg2) else 0
                for x in range(8):
                    bit = (b0 >> (7-x)) & 1
                    if bit: im.putpixel((x0+x, y0+y), 1)
                    bit2 = (b2 >> (7-x)) & 1
                    if bit2: im.putpixel((x0+8+x, y0+y), 2)
        im = im.resize((im.width*2, im.height*2), Image.Resampling.NEAREST)
        path = out_dir / f"da3800_stream_{sid:02d}_decoded_records_16x16_view.png"
        annotate(im, f"DA:3800 decoded stream {sid} records={len(recs)} left=seg0 right=seg2").save(path)
        paths.append(path)
    # combined contact sheet for first 12 streams
    thumbs = []
    for p in paths[:12]:
        im = Image.open(p).convert("RGB")
        # shrink if too large
        im.thumbnail((480, 240), Image.Resampling.NEAREST)
        thumbs.append((p.stem, im.copy()))
    if thumbs:
        cs = contact_sheet(thumbs, cols=2)
        cs_path = out_dir / "da3800_decoded_streams_contact_sheet.png"
        cs.save(cs_path)
        paths.append(cs_path)
    return paths


def make_zip(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src_dir.parent))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path, default=Path("shinmomo_graphics_probe_v1_out"))
    ap.add_argument("--da-csv", type=Path, default=None)
    ap.add_argument("--full", action="store_true", help="dump full ROM raw sheets")
    ap.add_argument("--zip", action="store_true")
    args = ap.parse_args()

    data = load_rom(args.rom)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    scores: List[WindowScore] = []
    for off in range(0, len(data) - 0x1000 + 1, 0x1000):
        scores.append(score_window(data, off, 2, 0x1000))
        scores.append(score_window(data, off, 4, 0x1000))
    write_scores_csv(scores, out / "shinmomo_graphics_window_scores_v1.csv")

    if args.full:
        dump_full_sheets(data, out / "01_full_raw_2bpp_sheets", 2, 0x4000)
        dump_full_sheets(data, out / "01_full_raw_4bpp_sheets", 4, 0x4000)

    dump_top_candidates(data, scores, out / "02_font_candidates", "font_2bpp", 2, "font_score", 32)
    dump_top_candidates(data, scores, out / "02_font_candidates", "font_4bpp", 4, "font_score", 16)
    dump_top_candidates(data, scores, out / "03_face_person_candidates", "face_person_4bpp", 4, "face_score", 32)
    dump_top_candidates(data, scores, out / "03_face_person_candidates", "face_person_2bpp", 2, "face_score", 16)
    dump_top_candidates(data, scores, out / "04_mapchip_candidates", "mapchip_4bpp", 4, "map_score", 32)
    dump_top_candidates(data, scores, out / "04_mapchip_candidates", "mapchip_2bpp", 2, "map_score", 16)
    render_known_regions(data, out / "05_known_reference_regions")
    if args.da_csv:
        render_da3800_decoded(args.da_csv, out / "06_da3800_decoded_stream_views")

    readme = out / "README_shinmomo_graphics_probe_v1.md"
    readme.write_text(f"""# 新桃太郎伝説 グラフィック調査 v1

## 実行内容

- ROMサイズ: {len(data):,} bytes
- 2bpp/4bpp raw tile scan window: 0x1000 bytes step
- full raw sheets: {'出力済み' if args.full else '未出力'}
- candidate CSV: `shinmomo_graphics_window_scores_v1.csv`

## フォルダ

- `01_full_raw_2bpp_sheets/`: ROM全域を2bpp raw tile sheet化
- `01_full_raw_4bpp_sheets/`: ROM全域を4bpp raw tile sheet化
- `02_font_candidates/`: フォント候補
- `03_face_person_candidates/`: 顔グラ/人物グラ候補
- `04_mapchip_candidates/`: マップチップ候補
- `05_known_reference_regions/`: 既知アドレス周辺の参考出力
- `06_da3800_decoded_stream_views/`: 既存DA:3800 decoded CSVからの小資材ビュー

## 注意

これは「生ROMをSNES tile形式として可視化する探索器」です。
圧縮グラフィックはこの方法だけでは正しく出ません。
見た目どおりに復元するには、Snes9xでVRAM/CGRAM/tilemap/OAMを実行時dumpし、CGRAM paletteとtilemap属性を適用してください。

## アドレス表記

ファイル名にはPC offsetとLoROM想定SNESアドレスを併記しています。
例: `pc026A60_84_EA60` はPC `0x026A60` / LoROM `84:EA60` 相当です。
""", encoding="utf-8")

    if args.zip:
        make_zip(out, out.with_suffix(".zip"))
        print(out.with_suffix(".zip"))
    else:
        print(out)


if __name__ == "__main__":
    main()
