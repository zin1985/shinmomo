#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/maps/rendered/catalog/map_render_catalog.csv"
TRANSITIONS = ROOT / "data/maps/transitions"
OUT = ROOT / "viewer/data/world.json"

def split_ids(value):
    return [x for x in (value or "").split(";") if x]

def main():
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8-sig")))
    maps = {}
    for row in rows:
        if row["artifact_role"] not in {"normal_primary", "mode7_primary"}:
            continue
        for config_id in split_ids(row["config_ids"]):
            maps[config_id] = {
                "config_id": config_id,
                "tileset_id": int(row["tileset_id"]),
                "layout_id": int(row["layout_id"]),
                "display_name": None,
                "pixel_width": int(row["image_width_px"] or 0),
                "pixel_height": int(row["image_height_px"] or 0),
                "render_kind": row["artifact_role"],
                "layers": [{
                    "kind": "structural_metatile",
                    "data": f"layers/t{int(row['tileset_id']):02d}_l{int(row['layout_id']):03d}.json",
                }],
                "entities": [],
                "confidence": row["confidence"],
                "provenance": "map_render_catalog",
            }
    transitions = []
    for path in sorted(TRANSITIONS.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("kind") != "runtime_map_transition_evidence":
            continue
        transitions.append({
            "transition_id": path.stem,
            "source_config_id": doc.get("from", {}).get("config_id"),
            "destination_config_id": doc.get("to", {}).get("config_id"),
            "trigger": doc.get("trigger_observation"),
            "status": doc.get("relation_status"),
            "destination_x": None,
            "destination_y": None,
            "provenance": str(path.relative_to(ROOT)).replace("\\", "/"),
        })

    world = {
        "schema_version": 1,
        "kind": "shinmomo_structural_world",
        "asset_profiles": {
            "canonical": {"visibility": "local_only", "fallback": False},
            "public_redrawn": {"visibility": "public", "fallback": False},
        },
        "maps": sorted(maps.values(), key=lambda x: x["config_id"]),
        "transitions": transitions,
        "events": [],
        "entities": [],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"maps={len(world['maps'])} bytes={OUT.stat().st_size}")

if __name__ == "__main__":
    main()
