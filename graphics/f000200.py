#!/usr/bin/env python3
# shinmomo_vram_snapshot_compare_20260501.py
#
# Usage:
#   python shinmomo_vram_snapshot_compare_20260501.py shinmomo_graphics_probe_out_v2
#
# Purpose:
#   Post-process Lua snapshot folders after moving through town / field / battle.
#   Produces cross-scene tile usage tables and compact BG layout summaries.
#
# Notes:
#   This does not need the ROM. It works from frame_*/bg*_tilemap.csv,
#   frame_*/bg*_tile_usage.csv, frame_*/bg_summary.csv, and vram.bin.

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path
from collections import defaultdict, Counter

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def sha1_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) >= 2 else Path("shinmomo_graphics_probe_out_v2")
    if not root.exists():
        print(f"ERROR: output dir not found: {root}", file=sys.stderr)
        return 2

    frames = sorted([p for p in root.iterdir() if p.is_dir() and p.name.startswith("frame_")])
    if not frames:
        print(f"ERROR: no frame_* folders in {root}", file=sys.stderr)
        return 2

    out = root / "analysis"
    out.mkdir(exist_ok=True)

    # 1) Compact per-frame BG layout summary.
    summary_rows = []
    for fr in frames:
        bg = read_csv(fr / "bg_summary.csv")
        scene = ""
        # v2 frame_summary has scene_label. Fallback to folder.
        fs = read_csv(root / "frame_summary.csv")
        frame_num = fr.name.replace("frame_", "")
        scene_by_frame = {r.get("frame", ""): r.get("scene_label", "") for r in fs}
        scene = scene_by_frame.get(str(int(frame_num)) if frame_num.isdigit() else frame_num, "")
        vram_hash = sha1_file(fr / "vram.bin")[:12]
        cgram_hash = sha1_file(fr / "cgram.bin")[:12]
        for r in bg:
            summary_rows.append({
                "frame_dir": fr.name,
                "scene_label": scene,
                "vram_sha1_12": vram_hash,
                "cgram_sha1_12": cgram_hash,
                "bg": r.get("bg", ""),
                "mode": r.get("mode", ""),
                "map_base": r.get("map_base", ""),
                "char_base": r.get("char_base", ""),
                "bpp": r.get("bpp", ""),
                "width_tiles": r.get("width_tiles", ""),
                "height_tiles": r.get("height_tiles", ""),
                "tm_main_screen": r.get("tm_main_screen", ""),
                "ts_sub_screen": r.get("ts_sub_screen", ""),
            })
    with (out / "cross_frame_bg_layout_summary.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["frame_dir","scene_label","vram_sha1_12","cgram_sha1_12","bg","mode","map_base","char_base","bpp","width_tiles","height_tiles","tm_main_screen","ts_sub_screen"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(summary_rows)

    # 2) Tile usage by BG/frame.
    tile_rows = []
    total_key_counter = Counter()
    for fr in frames:
        for bgno in range(1, 5):
            usage_path = fr / f"bg{bgno}_tile_usage.csv"
            rows = read_csv(usage_path)
            if not rows:
                # fallback: aggregate tilemap
                tm = read_csv(fr / f"bg{bgno}_tilemap.csv")
                agg = Counter()
                attrs = defaultdict(Counter)
                for r in tm:
                    t = r.get("tile", "")
                    if t == "":
                        continue
                    agg[t] += 1
                    attrs[t][f"p{r.get('palette','')}_r{r.get('priority','')}_h{r.get('hflip','')}_v{r.get('vflip','')}"] += 1
                rows = []
                for t, c in agg.items():
                    rows.append({
                        "bg": str(bgno),
                        "tile": t,
                        "count": str(c),
                        "attr_variants": " ".join(f"{k}:{v}" for k, v in sorted(attrs[t].items())),
                        "map_base": tm[0].get("map_base","") if tm else "",
                        "char_base": tm[0].get("char_base","") if tm else "",
                        "bpp": tm[0].get("bpp","") if tm else "",
                        "mode": tm[0].get("mode","") if tm else "",
                        "scene_label": ""
                    })
            for r in rows:
                key = (r.get("bg",""), r.get("char_base",""), r.get("bpp",""), r.get("tile",""))
                total_key_counter[key] += int(r.get("count","0") or 0)
                tile_rows.append({
                    "frame_dir": fr.name,
                    "bg": r.get("bg",""),
                    "scene_label": r.get("scene_label",""),
                    "char_base": r.get("char_base",""),
                    "bpp": r.get("bpp",""),
                    "tile": r.get("tile",""),
                    "count": r.get("count",""),
                    "attr_variants": r.get("attr_variants",""),
                    "map_base": r.get("map_base",""),
                    "mode": r.get("mode",""),
                })
    with (out / "cross_frame_tile_usage_long.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["frame_dir","scene_label","bg","mode","map_base","char_base","bpp","tile","count","attr_variants"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(tile_rows)

    # 3) Global tile ranking: useful for finding persistent mapchips.
    ranking = []
    for (bg, chrbase, bpp, tile), count in total_key_counter.most_common():
        ranking.append({"bg": bg, "char_base": chrbase, "bpp": bpp, "tile": tile, "total_count": count})
    with (out / "global_tile_usage_ranking.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["bg","char_base","bpp","tile","total_count"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(ranking)

    print(f"OK: wrote {out}")
    print("  - cross_frame_bg_layout_summary.csv")
    print("  - cross_frame_tile_usage_long.csv")
    print("  - global_tile_usage_ranking.csv")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
