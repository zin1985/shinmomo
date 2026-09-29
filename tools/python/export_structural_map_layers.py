#!/usr/bin/env python3
"""Export compact ROM map structure for the browser viewer.

ROM-derived pixels are deliberately excluded. Layout metatile IDs and CE
metatile definitions are structural data; rendering assets remain profile-specific.
"""
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/python"))
import decode_map_layout as dec

def used_ids(grid):
    return sorted({int(v) for row in grid for v in row})

def export_layout(rom, tileset_id, layout_id):
    layout = dec.parse_layout(rom, layout_id)
    grid = layout["grid"]
    ptr = dec.tileset_pointer(rom, tileset_id)
    definitions = {}
    for mid in used_ids(grid):
        base = ptr + mid * 8
        definitions[str(mid)] = [
            dec.u16_at(rom, 0xCE, base + i * 2) for i in range(4)
        ]
    return {
        "schema_version": 1,
        "tileset_id": tileset_id,
        "layout_id": layout_id,
        "metatile_width": len(grid[0]),
        "metatile_height": len(grid),
        "metatile_ids": [v for row in grid for v in row],
        "metatile_definitions": definitions,
        "tile_entry_format": "SNES_BG_16bit",
        "pixel_data_included": False,
        "provenance": {
            "layout_record": layout["record_ptr"],
            "tileset_block": f"CE:{ptr:04X}",
        },
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--tileset", type=int)
    ap.add_argument("--layout", type=int)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--catalog", type=Path)
    ap.add_argument("--out-dir", type=Path)
    a=ap.parse_args()
    rom=a.rom.read_bytes()
    if a.catalog:
        rows=list(csv.DictReader(a.catalog.open(encoding="utf-8-sig")))
        pairs=sorted({(int(r["tileset_id"]),int(r["layout_id"]))
            for r in rows if r["artifact_role"] in {"normal_primary","mode7_primary"}})
        a.out_dir.mkdir(parents=True,exist_ok=True)
        for ts,lid in pairs:
            doc=export_layout(rom,ts,lid)
            out=a.out_dir/f"t{ts:02d}_l{lid:03d}.json"
            out.write_text(json.dumps(doc,separators=(",",":")),encoding="utf-8")
        print("exported",len(pairs),"primary structural layers")
        return
    if a.tileset is None or a.layout is None or a.out is None:
        ap.error("single export requires --tileset, --layout and --out")
    doc=export_layout(rom,a.tileset,a.layout)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(doc,separators=(",",":")),encoding="utf-8")
    print(a.out,a.out.stat().st_size,"bytes",len(doc["metatile_definitions"]),"used metatiles")

if __name__=="__main__":
    main()
