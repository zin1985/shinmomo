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
        # Dungeon catalog rows can omit image dimensions even though their
        # structural layer and rendered PNG are already available.
        if not pixel_width:
            pixel_width = grid_width * 16
        if not pixel_height:
            pixel_height = grid_height * 16
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
                "transition_arrivals": [],
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

    transition_candidates = []
    transition_edges = []
    candidate_path = TRANSITIONS / "map_transition_candidates.csv"
    if candidate_path.exists():
        for n, row in enumerate(csv.DictReader(candidate_path.open(encoding="utf-8-sig"))):
            source_config_id = row.get("source_config_id") or None
            destination_config_id = row.get("destination_config_id") or None
            confidence = row.get("confidence") or "unknown"
            tier = "tier1_confirmed" if confidence == "confirmed" else (
                "tier2_strong_bound" if source_config_id and destination_config_id else "tier3_unbound"
            )
            item = {
                "transition_id": f"catalog_transition_{n:04d}",
                "tier": tier,
                "source_config_id": source_config_id,
                "source_pack": row.get("source_pack") or None,
                "source_layout": int(row["source_layout"]) if row.get("source_layout") else None,
                "source_tileset": int(row["source_tileset"]) if row.get("source_tileset") else None,
                "script_pack": row.get("script_pack") or None,
                "script_record": int(row["script_record"]) if row.get("script_record") else None,
                "script_entry": row.get("script_entry") or None,
                "trigger_type": row.get("trigger_type") or None,
                "trigger_addr": row.get("trigger_addr") or None,
                "event_record": row.get("event_record") or None,
                "vm_context": row.get("vm_context") or None,
                "event_sources": row.get("event_sources") or None,
                "destination_pack": row.get("destination_pack") or None,
                "destination_entry_id": row.get("destination_entry_id") or None,
                "destination_config_id": destination_config_id,
                "destination_layout": int(row["destination_layout"]) if row.get("destination_layout") else None,
                "destination_tileset": int(row["destination_tileset"]) if row.get("destination_tileset") else None,
                "destination_variant": int(row["destination_variant"]) if row.get("destination_variant") else None,
                "destination_x": int(row["destination_x"]) if row.get("destination_x") else None,
                "destination_y": int(row["destination_y"]) if row.get("destination_y") else None,
                "destination_secondary_x": int(row["destination_secondary_x"]) if row.get("destination_secondary_x") else None,
                "destination_secondary_y": int(row["destination_secondary_y"]) if row.get("destination_secondary_y") else None,
                "destination_coordinate_addr": row.get("destination_coordinate_addr") or None,
                "condition": row.get("condition") or None,
                "confidence": confidence,
                "evidence": row.get("evidence") or None,
                "provenance": row.get("provenance") or "data/maps/transitions/map_transition_candidates.csv",
            }
            transition_candidates.append(item)
            if source_config_id and destination_config_id:
                transition_edges.append(item)

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
            m = maps[config_id]
            primary = m["layers"][0]
            primary["bg"] = assignment.get("primary")
            # A BG1+BG2 composite is the most faithful canonical preview when
            # available; keep structural layers separately for inspection.
            if row.get("png"):
                m["canonical_image"] = f"../{row['png']}"
                m["render_kind"] = "bg12_composite"
                composite_w = int(row.get("image_width_px") or m["pixel_width"])
                composite_h = int(row.get("image_height_px") or m["pixel_height"])
                m["pixel_width"] = composite_w
                m["pixel_height"] = composite_h
                m["grid_cell_px_x"] = composite_w / m["grid_width"]
                m["grid_cell_px_y"] = composite_h / m["grid_height"]
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

    # Static opcode59 actor coordinates are proven for this renderer path only.
    # The shared WRAM columns must not be generalized to unrelated handlers.
    # Current corpus audit: every seed pair falls inside its mapped structural map grid.
    actor_seed_audit = {"rows": 0, "in_bounds": 0, "out_of_bounds": 0}
    selector_asset_alias = {}
    selector_display_meta = {}
    if SELECTOR_CATALOG.exists():
        for catalog_row in csv.DictReader(SELECTOR_CATALOG.open(encoding="utf-8-sig")):
            selector_hex = f"{int(catalog_row['selector']):02X}"
            duplicate = (catalog_row.get("duplicate_of") or "").replace("0x", "").upper()
            selector_asset_alias[selector_hex] = duplicate or selector_hex
            selector_display_meta[selector_hex] = {
                "display_frame": int(catalog_row["display_frame"]) if catalog_row.get("display_frame") else None,
                "display_orientation": catalog_row.get("display_orientation") or None,
            }
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
                "display_frame": selector_display_meta.get(selector_hex, {}).get("display_frame"),
                "display_orientation": selector_display_meta.get(selector_hex, {}).get("display_orientation"),
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

    # Destination coordinates are independently useful even when the static
    # source map remains unresolved. Group identical arrival points to avoid
    # rendering hundreds of duplicate markers in the HTML viewer.
    transition_arrivals = []
    candidate_path = TRANSITIONS / "map_transition_candidates.csv"
    grouped_arrivals = {}
    if candidate_path.exists():
        for row in csv.DictReader(candidate_path.open(encoding="utf-8-sig")):
            config_id = row.get("destination_config_id") or ""
            sx, sy = row.get("destination_x") or "", row.get("destination_y") or ""
            if config_id not in maps or not sx or not sy:
                continue
            gx, gy = int(sx), int(sy)
            key = (config_id, gx, gy)
            item = grouped_arrivals.setdefault(key, {
                "rows": 0, "destination_packs": set(), "destination_entries": set(),
                "confidences": set(), "source_configs": set(),
                "trigger_addrs": set(), "trigger_types": set(),
            })
            if row.get("destination_pack"): item["destination_packs"].add(row["destination_pack"])
            if row.get("destination_entry_id"): item["destination_entries"].add(row["destination_entry_id"])
            item["rows"] += 1
            if row.get("confidence"): item["confidences"].add(row["confidence"])
            if row.get("source_config_id"): item["source_configs"].add(row["source_config_id"])
            if row.get("trigger_addr"): item["trigger_addrs"].add(row["trigger_addr"])
            if row.get("trigger_type"): item["trigger_types"].add(row["trigger_type"])
    for n, (key, info) in enumerate(sorted(grouped_arrivals.items())):
        config_id, gx, gy = key
        m = maps[config_id]
        arrival = {
            "arrival_id": f"arrival_{n:04d}",
            "map_config_id": config_id,
            "destination_packs": sorted(info["destination_packs"]),
            "destination_entry_ids": sorted(info["destination_entries"]),
            "grid_x": gx, "grid_y": gy,
            "x": gx * m["grid_cell_px_x"],
            "y": gy * m["grid_cell_px_y"],
            "candidate_row_count": info["rows"],
            "confidence_classes": sorted(info["confidences"]),
            "source_config_ids": sorted(info["source_configs"]),
            "trigger_addrs": sorted(info["trigger_addrs"]),
            "trigger_types": sorted(info["trigger_types"]),
            "coordinate_status": "resolved_destination_entry_grid_coordinate",
            "provenance": "data/maps/transitions/map_transition_candidates.csv",
        }
        transition_arrivals.append(arrival)
        m["transition_arrivals"].append(arrival["arrival_id"])

    world = {
        "schema_version": 4,
        "kind": "shinmomo_structural_world",
        "asset_profiles": {
            "canonical": {"visibility": "local_only", "fallback": False},
            "public_redrawn": {"visibility": "public", "fallback": False},
        },
        "maps": sorted(maps.values(), key=lambda x: x["config_id"]),
        "transitions": transitions,
        "transition_candidates": transition_candidates,
        "transition_edges": transition_edges,
        "transition_catalog_summary": {
            "candidate_count": len(transition_candidates),
            "confirmed_count": sum(x["confidence"] == "confirmed" for x in transition_candidates),
            "strong_candidate_count": sum(x["confidence"] == "strong_candidate" for x in transition_candidates),
            "bound_edge_count": len(transition_edges),
            "unbound_count": sum(not x["source_config_id"] for x in transition_candidates),
        },
        "events": events,
        "sprite_groups": sprite_groups,
        "entities": entities,
        "transition_arrivals": transition_arrivals,
        "transition_arrival_summary": {
            "group_count": len(transition_arrivals),
            "plotted_candidate_rows": sum(x["candidate_row_count"] for x in transition_arrivals),
        },
        "actor_seed_position_audit": actor_seed_audit,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"maps={len(world['maps'])} bytes={OUT.stat().st_size}")

if __name__ == "__main__":
    main()
