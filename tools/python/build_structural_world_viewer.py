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

    composites = [r for r in rows if r["artifact_role"] == "bg12_composite"]
    for row in composites:
        for config_id in split_ids(row["config_ids"]):
            if config_id not in maps:
                continue
            assignment = {}
            for part in row["bg_assignment"].split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    assignment[k] = v
            primary = maps[config_id]["layers"][0]
            primary["bg"] = assignment.get("primary")
            secondary = {
                "kind": "structural_metatile",
                "role": "secondary",
                "bg": assignment.get("secondary"),
                "tileset_id": int(row["secondary_tileset_id"]),
                "layout_id": int(row["secondary_layout_id"]),
                "data": f"layers/t{int(row['secondary_tileset_id']):02d}_l{int(row['secondary_layout_id']):03d}.json",
                "confidence": row["confidence"],
            }
            if not any(x.get("role") == "secondary" for x in maps[config_id]["layers"]):
                maps[config_id]["layers"].append(secondary)

    events = []
    event_path = ROOT / "data/events/event_record_frame_catalog.csv"
    source_path = ROOT / "data/events/event_source_crosslink.csv"
    map_event_path = ROOT / "data/maps/context/map_dialogue_pack_crosslink.csv"
    source_counts = {}
    if source_path.exists():
        for row in csv.DictReader(source_path.open(encoding="utf-8-sig")):
            source_counts[row["record_id"]] = source_counts.get(row["record_id"], 0) + 1
    events_by_family = {}
    if event_path.exists():
        for row in csv.DictReader(event_path.open(encoding="utf-8-sig")):
            event = {
                "event_id": row["record_id"],
                "family_id": int(row["family_id"]),
                "record_start": row["record_start"],
                "record_end_exclusive": row["record_end_exclusive"],
                "source_link_count": source_counts.get(row["record_id"], 0),
                "evidence_class": row["evidence_class"],
                "semantic_status": row["semantic_status"],
            }
            events.append(event)
            events_by_family.setdefault(int(row["family_id"]), []).append(row["record_id"])
    if map_event_path.exists():
        for row in csv.DictReader(map_event_path.open(encoding="utf-8-sig")):
            config_id = row["config_id"]
            family = int(row["source_family_hex"], 16)
            if config_id in maps and family in events_by_family:
                refs = maps[config_id].setdefault("event_families", [])
                if not any(x["family_id"] == family for x in refs):
                    refs.append({
                        "family_id": family,
                        "event_ids": events_by_family[family],
                        "relation": "pack_family_context",
                        "provenance": "map_dialogue_pack_crosslink",
                    })

    sprite_groups = []
    sprite_path = ROOT / "data/npc_display/shinmomo_B294_sprite_groups_summary_20260425.csv"
    if sprite_path.exists():
        for row in csv.DictReader(sprite_path.open(encoding="utf-8-sig")):
            sprite_groups.append({
                "sprite_group_id": int(row["group"]),
                "pointer": row["pointer"],
                "first_frame_ptr": row["first_frame_ptr"],
                "inferred_frame_pointer_count": int(row["inferred_pointer_entries_until_first_frame"]),
                "first_frame_piece_count": int(row["first_frame_piece_count"]),
                "provenance": str(sprite_path.relative_to(ROOT)).replace("\\", "/"),
                "binding_status": "asset_only_unbound_to_map_entity",
            })

    entities = []
    entity_dir = ROOT / "data/entities"
    if entity_dir.exists():
        for path in sorted(entity_dir.glob("runtime_entity_observation_*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            if doc.get("kind") != "runtime_logical_entity_observation":
                continue
            for object_id in doc.get("logical_object_ids", []):
                entity = {
                    "entity_id": f"{path.stem}_obj{object_id:02X}",
                    "map_config_id": doc["config_id"],
                    "logical_object_id": object_id,
                    "entity_type": doc.get("semantic_classification"),
                    "x": None,
                    "y": None,
                    "sprite_group": None,
                    "event_refs": [],
                    "confidence": doc["confidence"],
                    "provenance": str(path.relative_to(ROOT)).replace("\\", "/"),
                }
                entities.append(entity)
                if doc["config_id"] in maps:
                    maps[doc["config_id"]]["entities"].append(entity["entity_id"])

    world = {
        "schema_version": 1,
        "kind": "shinmomo_structural_world",
        "asset_profiles": {
            "canonical": {"visibility": "local_only", "fallback": False},
            "public_redrawn": {"visibility": "public", "fallback": False},
        },
        "maps": sorted(maps.values(), key=lambda x: x["config_id"]),
        "transitions": transitions,
        "events": events,
        "sprite_groups": sprite_groups,
        "entities": entities,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"maps={len(world['maps'])} bytes={OUT.stat().st_size}")

if __name__ == "__main__":
    main()
