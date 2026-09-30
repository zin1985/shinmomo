#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/maps/rendered/catalog/map_render_catalog.csv"
TRANSITIONS = ROOT / "data/maps/transitions"
OUT = ROOT / "viewer/data/world.json"
SELECTOR_CATALOG = ROOT / "data/npc_display/static_character_selector_catalog_20260930.csv"

def split_ids(value):
    return [x for x in (value or "").split(";") if x]

def layer_grid_dimensions(tileset_id, layout_id, pixel_width, pixel_height):
    path = ROOT / "viewer/data/layers" / f"t{tileset_id:02d}_l{layout_id:03d}.json"
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        return int(doc["metatile_width"]), int(doc["metatile_height"])
    return max(1, pixel_width // 16), max(1, pixel_height // 16)

def main():
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8-sig")))
    maps = {}
    for row in rows:
        if row["artifact_role"] not in {"normal_primary", "mode7_primary"}:
            continue
        tileset_id = int(row["tileset_id"])
        layout_id = int(row["layout_id"])
        pixel_width = int(row["image_width_px"] or 0)
        pixel_height = int(row["image_height_px"] or 0)
        grid_width, grid_height = layer_grid_dimensions(tileset_id, layout_id, pixel_width, pixel_height)
        for config_id in split_ids(row["config_ids"]):
            maps[config_id] = {
                "config_id": config_id,
                "tileset_id": tileset_id,
                "layout_id": layout_id,
                "display_name": row.get("display_names") or None,
                "pixel_width": pixel_width,
                "pixel_height": pixel_height,
                "grid_width": grid_width,
                "grid_height": grid_height,
                "grid_cell_px_x": pixel_width / grid_width,
                "grid_cell_px_y": pixel_height / grid_height,
                "canonical_image": f"../{row['png']}" if row.get("png") else None,
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

    # Visible object observations are a separate engine layer from $1569 logical actors.
    # Only nonzero frame-state objects are promoted to viewer entities for now.
    if entity_dir.exists():
        for path in sorted(entity_dir.glob("runtime_visible_objects_*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            if doc.get("kind") != "runtime_visible_object_observation":
                continue
            for obj in doc.get("objects", []):
                if not obj.get("renderable_frame_nonzero"):
                    continue
                entity = {
                    "entity_id": f"{path.stem}_slot{obj['slot']:02X}",
                    "map_config_id": doc["config_id"],
                    "logical_object_id": None,
                    "visible_slot": obj["slot"],
                    "entity_type": None,
                    "x": obj["x"],
                    "y": obj["y"],
                    "coordinate_space": doc.get("coordinate_space"),
                    "sprite_group": obj["sprite_group_index"],
                    "sprite_group_raw": obj["sprite_group_raw"],
                    "frame_state": obj["frame_state"],
                    "event_refs": [],
                    "confidence": doc["confidence"],
                    "provenance": str(path.relative_to(ROOT)).replace("\\", "/"),
                }
                entities.append(entity)
                if doc["config_id"] in maps:
                    maps[doc["config_id"]]["entities"].append(entity["entity_id"])

    # Static opcode59 actor bindings carry two placement-like seed bytes.
    # Their universal semantics are not proven yet, so expose them as a candidate layer only.
    # Current corpus audit: every seed pair falls inside its mapped structural map grid.
    actor_seed_audit = {"rows": 0, "in_bounds": 0, "out_of_bounds": 0}
    selector_asset_alias = {}
    if SELECTOR_CATALOG.exists():
        for catalog_row in csv.DictReader(SELECTOR_CATALOG.open(encoding="utf-8-sig")):
            selector_hex = f"{int(catalog_row['selector']):02X}"
            duplicate = (catalog_row.get("duplicate_of") or "").replace("0x", "").upper()
            selector_asset_alias[selector_hex] = duplicate or selector_hex
    static_actor_path = ROOT / "data/npc_display/static_map_actor_selector_crosslink_20260930.csv"
    if static_actor_path.exists():
        seen = set()
        for row in csv.DictReader(static_actor_path.open(encoding="utf-8-sig")):
            config_id = row["config_id"]
            key = (config_id, row["record_id"], row["selector_hex"])
            if config_id not in maps or key in seen:
                continue
            seen.add(key)
            gx = int(row["field_0659_seed"])
            gy = int(row["field_0699_seed"])
            m = maps[config_id]
            grid_w = m["grid_width"]
            grid_h = m["grid_height"]
            in_bounds = 0 <= gx < grid_w and 0 <= gy < grid_h
            actor_seed_audit["rows"] += 1
            actor_seed_audit["in_bounds" if in_bounds else "out_of_bounds"] += 1
            selector_hex = row["selector_hex"].replace("0x", "").upper().zfill(2)
            asset_selector_hex = selector_asset_alias.get(selector_hex, selector_hex)
            entity = {
                "entity_id": f"static_actor_{config_id}_{row['record_id']}_{selector_hex}",
                "map_config_id": config_id,
                "entity_type": "static_actor_candidate",
                "record_id": row["record_id"],
                "selector_hex": f"0x{selector_hex}",
                "sprite_group": int(row["sprite_group"]),
                "animation_base_state": int(row["animation_base_state"]),
                "grid_x_seed": gx,
                "grid_y_seed": gy,
                "x": gx * m["grid_cell_px_x"],
                "y": gy * m["grid_cell_px_y"],
                "coordinate_space": "opcode59_actor_map_grid",
                "coordinate_status": "confirmed_opcode59_actor_renderer_grid_coordinates",
                "sprite_anchor_status": "viewer_bottom_center_approximation",
                "sprite_asset_selector_hex": f"0x{asset_selector_hex}",
                "sprite_asset": f"../graphics/static_character_reconstruction/catalog_selector_{asset_selector_hex}.png",
                "binding_evidence": row["binding_evidence"],
                "position_evidence": [
                    "C1:B07E copies $0659/$0699 to $030B/$030D",
                    "81:B10F converts $030B/$030D to 16px render coordinates relative to $1573/$157D",
                    "817/817 static actor seed pairs fall inside their mapped structural grid",
                ],
                "confidence": "confirmed_static_opcode59_coordinate_path",
                "provenance": str(static_actor_path.relative_to(ROOT)).replace("\\", "/"),
            }
            entities.append(entity)
            m["entities"].append(entity["entity_id"])

    world = {
        "schema_version": 2,
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
        "actor_seed_position_audit": actor_seed_audit,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"maps={len(world['maps'])} bytes={OUT.stat().st_size}")

if __name__ == "__main__":
    main()
