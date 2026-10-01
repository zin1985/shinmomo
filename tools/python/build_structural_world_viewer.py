#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/maps/rendered/catalog/map_render_catalog.csv"
TRANSITIONS = ROOT / "data/maps/transitions"
OUT = ROOT / "viewer/data/world.json"
SELECTOR_CATALOG = ROOT / "data/npc_display/static_character_selector_catalog_20260930.csv"
DIALOGUE_BINDING = ROOT / "data/npc_display/static_actor_event_dialogue_binding_20260930.csv"
DIALOGUE_SEQUENCE_CATALOG = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
SPRITE_SEMANTICS = ROOT / "data/npc_display/static_actor_sprite_semantics_20260930.csv"
DIRECTIONAL_CATALOG = ROOT / "data/npc_display/static_character_directional_catalog_20260930.csv"
SOURCE_HOTSPOTS = TRANSITIONS / "source_transition_hotspots.csv"
LOCATION_CANDIDATES = ROOT / "data/maps/context/map_location_identity_candidates_20260930.csv"
ACTOR_SPAWN_CONDITIONS = ROOT / "data/npc_display/static_actor_spawn_conditions_20260930.csv"
ACTOR_SPAWN_PREDICATE_TERMS = ROOT / "data/npc_display/static_actor_spawn_predicate_terms_20260930.csv"
SCENE_STATE_REQUIREMENTS = ROOT / "data/npc_display/static_scene_state_requirements_20260930.json"

def split_ids(value):
    return [x for x in (value or "").split(";") if x]

def layer_grid_dimensions(tileset_id, layout_id, pixel_width, pixel_height):
    path = ROOT / "viewer/data/layers" / f"t{tileset_id:02d}_l{layout_id:03d}.json"
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        return int(doc["metatile_width"]), int(doc["metatile_height"])
    return max(1, pixel_width // 16), max(1, pixel_height // 16)

def dialogue_page_candidates(text):
    """Preserve decoder line breaks while exposing quote-delimited window candidates."""
    text = (text or "").replace("\r\n", "\n").replace("<00>", "").strip()
    if not text:
        return []
    pages = []
    pos = 0
    while True:
        start = text.find("「", pos)
        if start < 0:
            break
        end = text.find("」", start + 1)
        if end < 0:
            break
        page = text[start:end + 1].strip()
        if page:
            pages.append(page)
        pos = end + 1
    if pages:
        return pages
    return [x.strip() for x in text.split("\n\n") if x.strip()]

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
                "source_transition_hotspots": [],
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

    source_transition_hotspots = []
    if SOURCE_HOTSPOTS.exists():
        for row in csv.DictReader(SOURCE_HOTSPOTS.open(encoding="utf-8-sig", newline="")):
            source_config_id = row.get("source_config_id") or None
            hotspot = {
                "hotspot_id": row.get("hotspot_id"),
                "source_config_id": source_config_id,
                "source_grid_x": int(row["source_grid_x"]) if row.get("source_grid_x") else None,
                "source_grid_y": int(row["source_grid_y"]) if row.get("source_grid_y") else None,
                "source_width": int(row["source_width"]) if row.get("source_width") else 1,
                "source_height": int(row["source_height"]) if row.get("source_height") else 1,
                "hotspot_type": row.get("hotspot_type") or None,
                "trigger_type": row.get("trigger_type") or None,
                "trigger_addr": row.get("trigger_addr") or None,
                "event_record": row.get("event_record") or None,
                "transition_id": row.get("transition_id") or None,
                "destination_config_id": row.get("destination_config_id") or None,
                "destination_x": int(row["destination_x"]) if row.get("destination_x") else None,
                "destination_y": int(row["destination_y"]) if row.get("destination_y") else None,
                "confidence": row.get("confidence") or "unknown",
                "evidence": row.get("evidence") or None,
                "provenance": row.get("provenance") or str(SOURCE_HOTSPOTS.relative_to(ROOT)).replace("\\", "/"),
            }
            source_transition_hotspots.append(hotspot)
            if source_config_id in maps:
                maps[source_config_id]["source_transition_hotspots"].append(hotspot["hotspot_id"])

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

    dialogue_sequences = []
    dialogue_by_actor = {}
    canonical_sequence_ids = set()

    # Prefer the reproducible page-level sequence catalog when available. It
    # preserves explicit 0x01 line breaks and quote-delimited page candidates.
    if DIALOGUE_SEQUENCE_CATALOG.exists():
        doc = json.loads(DIALOGUE_SEQUENCE_CATALOG.read_text(encoding="utf-8"))
        for actor in doc.get("actors", []):
            actor_pack = actor.get("pack_id_hex") or ""
            actor_scene = actor.get("scene_id") or (
                f'{actor.get("config_id","")}@{actor_pack}' if actor_pack else ""
            )
            key = (
                actor_scene,
                actor.get("record_id") or "",
                actor.get("selector_hex") or "",
            )
            for seq in actor.get("dialogue_sequences", []):
                source = seq.get("source") or {}
                event = seq.get("event") or {}
                condition = seq.get("condition") or {}
                sequence_id = seq.get("sequence_id")
                item = {
                    "dialogue_sequence_id": sequence_id,
                    "scene_id": actor_scene or None,
                    "pack_id_hex": actor_pack or None,
                    "scene_context": seq.get("scene_context") or {
                        "scene_id": actor_scene or None,
                        "config_id": actor.get("config_id") or None,
                        "pack_id_hex": actor_pack or None,
                        "state_evaluation": "required_for_current_dialogue_selection",
                    },
                    "config_id": actor.get("config_id") or None,
                    "record_id": actor.get("record_id") or None,
                    "selector_hex": actor.get("selector_hex") or None,
                    "controller_pointer": actor.get("controller_pointer") or None,
                    "event_record": event.get("record_id") or None,
                    "event_source": source.get("text_pointer") or None,
                    "event_source_addr": source.get("text_pointer") or None,
                    "dialogue_command_addr": event.get("dialogue_command_addr") or None,
                    "text_record_id": source.get("text_record_id") or None,
                    "text_pointer": source.get("text_pointer") or None,
                    "decoded_text": "\n\n".join(
                        p.get("page_text", "") for p in seq.get("pages", []) if p.get("page_text")
                    ) or None,
                    "decode_status": source.get("decode_status") or None,
                    "condition": condition.get("description") or None,
                    "condition_status": condition.get("status") or None,
                    "condition_detail": condition,
                    "binding_status": seq.get("sequence_kind") or None,
                    "confidence": seq.get("confidence") or None,
                    "evidence": seq.get("evidence") or None,
                    "provenance": seq.get("provenance") or str(DIALOGUE_SEQUENCE_CATALOG.relative_to(ROOT)).replace("\\", "/"),
                    "pages": [
                        {
                            "page_index": page.get("page_index"),
                            "display_order": page.get("display_order"),
                            "text": page.get("page_text") or "",
                            "lines": page.get("lines") or [],
                            "line_count": page.get("line_count"),
                            "page_status": (page.get("page_boundary") or {}).get("status"),
                            "page_boundary": page.get("page_boundary"),
                            "advance": page.get("advance"),
                            "source_token_span": page.get("source_token_span"),
                        }
                        for page in seq.get("pages", [])
                    ],
                    "page_segmentation_status": "reproducible_sequence_catalog",
                    "choice_status": seq.get("choice_status"),
                    "choices": seq.get("choices") or [],
                    "branch_target": seq.get("branch_target"),
                    "termination": seq.get("termination"),
                    "variant_order": seq.get("variant_order"),
                    "sequence_kind": seq.get("sequence_kind"),
                }
                dialogue_sequences.append(item)
                dialogue_by_actor.setdefault(key, []).append(sequence_id)
                canonical_sequence_ids.add(sequence_id)

    # Keep event/source bindings for the broader actor corpus even when no
    # page-level text reconstruction exists yet.
    if DIALOGUE_BINDING.exists():
        for n, row in enumerate(csv.DictReader(DIALOGUE_BINDING.open(encoding="utf-8-sig", newline=""))):
            row_pack = row.get("pack_id_hex") or ""
            row_scene = row.get("scene_id") or (
                f'{row.get("config_id","")}@{row_pack}' if row_pack else ""
            )
            key = (row_scene, row.get("record_id") or "", row.get("selector_hex") or "")
            sequence_id = (
                f'{row.get("config_id")}:{row.get("record_id")}:{row.get("text_record_id")}'
                if row.get("text_record_id")
                else f'binding_{n:04d}'
            )
            if sequence_id in canonical_sequence_ids:
                continue
            decoded_text = row.get("decoded_text") or ""
            page_texts = dialogue_page_candidates(decoded_text)
            condition_text = row.get("condition") or ""
            if condition_text.startswith("multiple source selections"):
                fallback_condition_status = "predicate_unresolved_static"
                branch_selection_policy = "preserve_all_candidates_until_state_resolved"
            elif condition_text == "single validated source selection":
                fallback_condition_status = "single_validated_source_selection"
                branch_selection_policy = "single_source_no_branch_selection"
            elif condition_text:
                fallback_condition_status = "unresolved_static"
                branch_selection_policy = "preserve_all_candidates_until_state_resolved"
            else:
                fallback_condition_status = None
                branch_selection_policy = "unknown"
            item = {
                "dialogue_sequence_id": sequence_id,
                "scene_id": row_scene or None,
                "pack_id_hex": row_pack or None,
                "scene_context": {
                    "scene_id": row_scene or None,
                    "config_id": row.get("config_id") or None,
                    "pack_id_hex": row_pack or None,
                    "state_evaluation": "required_for_current_dialogue_selection",
                },
                "config_id": row.get("config_id") or None,
                "record_id": row.get("record_id") or None,
                "selector_hex": row.get("selector_hex") or None,
                "controller_pointer": row.get("controller_pointer") or None,
                "event_record": row.get("event_record") or None,
                "event_source": row.get("event_source") or None,
                "event_source_addr": row.get("event_source_addr") or None,
                "dialogue_command_addr": row.get("dialogue_command_addr") or None,
                "text_record_id": row.get("text_record_id") or None,
                "text_pointer": row.get("text_pointer") or None,
                "decoded_text": decoded_text or None,
                "decode_status": row.get("decode_status") or None,
                "condition": condition_text or None,
                "condition_status": fallback_condition_status,
                "branch_selection_policy": branch_selection_policy,
                "binding_status": row.get("binding_status") or None,
                "confidence": row.get("confidence") or None,
                "evidence": row.get("evidence") or None,
                "provenance": row.get("provenance") or str(DIALOGUE_BINDING.relative_to(ROOT)).replace("\\", "/"),
                "pages": [
                    {
                        "page_index": i + 1,
                        "display_order": i + 1,
                        "text": page,
                        "page_status": "fallback_decoder_candidate_page",
                    }
                    for i, page in enumerate(page_texts)
                ],
                "page_segmentation_status": "fallback_binding_decoder",
            }
            dialogue_sequences.append(item)
            dialogue_by_actor.setdefault(key, []).append(sequence_id)

    dialogue_sequence_by_id = {x["dialogue_sequence_id"]: x for x in dialogue_sequences}

    sprite_semantics = {}
    if SPRITE_SEMANTICS.exists():
        for row in csv.DictReader(SPRITE_SEMANTICS.open(encoding="utf-8-sig", newline="")):
            key = (row.get("config_id") or "", row.get("record_id") or "", row.get("selector_hex") or "")
            sprite_semantics[key] = {
                "semantic_role": row.get("semantic_role") or None,
                "character_name": row.get("character_name") or None,
                "appearance_class": row.get("appearance_class") or None,
                "confidence": row.get("confidence") or None,
                "evidence": row.get("evidence") or None,
                "provenance": row.get("provenance") or None,
            }

    directional_by_selector = {}
    if DIRECTIONAL_CATALOG.exists():
        for row in csv.DictReader(DIRECTIONAL_CATALOG.open(encoding="utf-8-sig", newline="")):
            selector_hex = row.get("selector_hex") or ""
            directional_by_selector[selector_hex] = {
                "sprite_group": int(row["sprite_group"]) if row.get("sprite_group") else None,
                "base_state": int(row["base_state"]) if row.get("base_state") else None,
                "right_state": int(row["right_state"]) if row.get("right_state") else None,
                "right_frames": row.get("right_frames") or None,
                "front_state": int(row["front_state"]) if row.get("front_state") else None,
                "front_frames": row.get("front_frames") or None,
                "left_state": int(row["left_state"]) if row.get("left_state") else None,
                "left_frames": row.get("left_frames") or None,
                "back_state": int(row["back_state"]) if row.get("back_state") else None,
                "back_frames": row.get("back_frames") or None,
                "walk_animation": row.get("walk_animation") or None,
                "idle_state": int(row["idle_state"]) if row.get("idle_state") else None,
                "idle_frames": row.get("idle_frames") or None,
                "sprite_alias": row.get("sprite_alias") or None,
                "direction_binding_status": row.get("direction_binding_status") or None,
                "confidence": row.get("confidence") or None,
                "evidence": row.get("evidence") or None,
                "provenance": row.get("provenance") or None,
            }

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
    location_candidates_by_context = {}
    if LOCATION_CANDIDATES.exists():
        for row in csv.DictReader(LOCATION_CANDIDATES.open(encoding="utf-8-sig", newline="")):
            key = (row.get("config_id") or "", row.get("pack_id_hex") or "")
            location_candidates_by_context.setdefault(key, []).append({
                "candidate_label": row.get("candidate_label") or None,
                "status": row.get("candidate_status") or "candidate",
                "runtime_identity_status": row.get("runtime_identity_status") or None,
                "limitation": row.get("limitation") or None,
                "promotion_rule": row.get("promotion_rule") or None,
                "provenance": row.get("provenance") or str(LOCATION_CANDIDATES.relative_to(ROOT)).replace("\\", "/"),
            })

    spawn_predicate_terms_by_actor = {}
    if ACTOR_SPAWN_PREDICATE_TERMS.exists():
        for row in csv.DictReader(ACTOR_SPAWN_PREDICATE_TERMS.open(encoding="utf-8-sig", newline="")):
            key = (row.get("scene_id") or "", row.get("record_id") or "", row.get("selector_hex") or "")
            spawn_predicate_terms_by_actor.setdefault(key, []).append({
                "term_order": int(row["term_order"]),
                "source_bytecode": row.get("source_bytecode") or None,
                "producer": row.get("producer") or None,
                "subtype_or_key": row.get("subtype_or_key") or None,
                "operand_id_hex": row.get("operand_id_hex") or None,
                "mask_bit_index": int(row["mask_bit_index"]),
                "bitset_base_wram": row.get("bitset_base_wram") or None,
                "wram": row.get("resolved_wram") or None,
                "bit": int(row["resolved_bit"]),
                "expected_value": int(row["expected_value"]),
                "term_expr": row.get("term_expr") or None,
                "condition_status": row.get("condition_status") or None,
                "handler_chain": row.get("handler_chain") or None,
                "evidence": row.get("evidence") or None,
                "provenance": str(ACTOR_SPAWN_PREDICATE_TERMS.relative_to(ROOT)).replace("\\", "/"),
            })
    for terms in spawn_predicate_terms_by_actor.values():
        terms.sort(key=lambda x: x["term_order"])

    spawn_conditions_by_actor = {}
    if ACTOR_SPAWN_CONDITIONS.exists():
        for row in csv.DictReader(ACTOR_SPAWN_CONDITIONS.open(encoding="utf-8-sig", newline="")):
            key = (row.get("scene_id") or "", row.get("record_id") or "", row.get("selector_hex") or "")
            spawn_conditions_by_actor[key] = {
                "guard_kind": row.get("guard_kind") or None,
                "branch_opcode": row.get("branch_opcode") or None,
                "branch_rel8": row.get("branch_rel8") or None,
                "branch_semantics": row.get("branch_semantics") or None,
                "predicate_bytecode": row.get("predicate_bytecode") or None,
                "producer_kind": row.get("producer_kind") or None,
                "producer_operand": row.get("producer_operand") or None,
                "condition_status": row.get("condition_status") or None,
                "condition_expr": row.get("condition_expr") or None,
                "flag_spec_hex": row.get("flag_spec_hex") or None,
                "flag_wram": row.get("flag_wram") or None,
                "flag_bit": int(row["flag_bit"]) if row.get("flag_bit") else None,
                "state_evaluation": row.get("state_evaluation") or None,
                "visibility_when_state_unknown": row.get("visibility_when_state_unknown") or None,
                "evidence": row.get("evidence") or None,
                "provenance": str(ACTOR_SPAWN_CONDITIONS.relative_to(ROOT)).replace("\\", "/"),
            }

    static_actor_path = ROOT / "data/npc_display/static_map_actor_selector_crosslink_20260930.csv"
    if static_actor_path.exists():
        seen = set()
        for row in csv.DictReader(static_actor_path.open(encoding="utf-8-sig")):
            config_id = row["config_id"]
            pack_id = row.get("pack_id_hex") or ""
            scene_id = f"{config_id}@{pack_id}" if pack_id else ""
            key = (scene_id, row["record_id"], row["selector_hex"])
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
            selector_key = f"0x{selector_hex}"
            asset_selector_hex = selector_asset_alias.get(selector_hex, selector_hex)
            semantic_key = (config_id, row["record_id"], selector_key)
            actor_key = (scene_id, row["record_id"], selector_key)
            semantic = sprite_semantics.get(semantic_key)
            directional = directional_by_selector.get(selector_key)
            actor_dialogue_refs = dialogue_by_actor.get(actor_key, [])
            spawn_condition = spawn_conditions_by_actor.get(actor_key)
            spawn_terms = spawn_predicate_terms_by_actor.get(actor_key, [])
            if spawn_condition and spawn_terms:
                spawn_condition = {**spawn_condition, "terms": spawn_terms}
            entity = {
                "entity_id": f"static_actor_{config_id}_{row['record_id']}_{selector_hex}",
                "map_config_id": config_id,
                "scene_id": scene_id or None,
                "pack_id_hex": pack_id or None,
                "location_label": row.get("map_label") or None,
                "location_label_status": "source_label" if row.get("map_label") else "unresolved",
                "location_candidates": location_candidates_by_context.get(
                    (config_id, row.get("pack_id_hex") or ""), []
                ),
                "entity_type": "static_actor_candidate",
                "record_id": row["record_id"],
                "selector_hex": selector_key,
                "sprite_group": int(row["sprite_group"]),
                "sprite_semantics": semantic,
                "directional_sprite": directional,
                "dialogue_refs": actor_dialogue_refs,
                "spawn_condition": spawn_condition,
                "spawn_visibility_status": ("unconditional_visible" if spawn_condition and spawn_condition.get("visibility_when_state_unknown") == "visible" else "conditional_candidate_state_unknown" if spawn_condition else "spawn_condition_unavailable"),
                "event_refs": sorted({
                    dialogue_sequence_by_id[ref]["event_record"]
                    for ref in actor_dialogue_refs
                    if ref in dialogue_sequence_by_id and dialogue_sequence_by_id[ref].get("event_record")
                }),
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
        "schema_version": 7,
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
        "dialogue_sequences": dialogue_sequences,
        "dialogue_summary": {
            "sequence_count": len(dialogue_sequences),
            "decoded_sequence_count": sum(bool(x["pages"]) for x in dialogue_sequences),
            "actor_binding_count": len(dialogue_by_actor),
            "binding_key": "scene_id + record_id + selector_hex",
            "scene_context_preserved": True,
        },
        "sprite_groups": sprite_groups,
        "entities": entities,
        "source_transition_hotspots": source_transition_hotspots,
        "source_transition_hotspot_summary": {
            "hotspot_count": len(source_transition_hotspots),
            "confirmed_count": sum(x["confidence"].startswith("confirmed") for x in source_transition_hotspots),
            "navigable_count": sum(bool(x["destination_config_id"]) for x in source_transition_hotspots),
        },
        "transition_arrivals": transition_arrivals,
        "transition_arrival_summary": {
            "group_count": len(transition_arrivals),
            "plotted_candidate_rows": sum(x["candidate_row_count"] for x in transition_arrivals),
        },
        "actor_seed_position_audit": actor_seed_audit,
        "scene_state_requirements": (json.loads(SCENE_STATE_REQUIREMENTS.read_text(encoding="utf-8")) if SCENE_STATE_REQUIREMENTS.exists() else None),
        "actor_spawn_condition_summary": {
            "catalog_row_count": len(spawn_conditions_by_actor),
            "unconditional_actor_count": sum(1 for e in entities if e.get("entity_type") == "static_actor_candidate" and (e.get("spawn_condition") or {}).get("visibility_when_state_unknown") == "visible"),
            "conditional_or_unresolved_actor_count": sum(1 for e in entities if e.get("entity_type") == "static_actor_candidate" and (e.get("spawn_condition") or {}).get("visibility_when_state_unknown") == "candidate"),
            "state_unknown_policy": "render conditional actors as candidates; do not assert current visibility",
            "binding_key": "scene_id + record_id + selector_hex",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"maps={len(world['maps'])} bytes={OUT.stat().st_size}")

if __name__ == "__main__":
    main()
