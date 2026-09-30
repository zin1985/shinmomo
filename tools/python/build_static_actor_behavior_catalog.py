#!/usr/bin/env python3
from pathlib import Path
import csv, json, collections

ROOT = Path(__file__).resolve().parents[2]
NPC = ROOT / "data/npc_display"
EVENTS = ROOT / "data/events"
VIEWER = ROOT / "viewer/data"

VALID_BINDING_STATUSES = {
    "actor_to_event_source_static",
    "actor_to_event_dialogue_static_cfg",
}

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

actors = read_csv(NPC / "static_map_actor_selector_crosslink_20260930.csv")
bindings = read_csv(NPC / "static_actor_event_dialogue_binding_20260930.csv")
visual_rows = read_csv(NPC / "static_map_bound_selector_visual_form_20260930.csv")
frames = read_csv(EVENTS / "event_record_frame_catalog.csv")
semantics = read_csv(NPC / "static_actor_sprite_semantics_20260930.csv")
motion = read_csv(NPC / "actor_motion_direction_pattern_table_20260930.csv")
spawn_rows = read_csv(NPC / "static_actor_spawn_conditions_20260930.csv")

visual_by_selector = {r["selector_hex"]: r for r in visual_rows}
frame_by_record = {r["record_id"]: r for r in frames}
semantic_by_key = {
    (r["config_id"], r["record_id"], r["selector_hex"]): r for r in semantics
}
facing_by_pattern = {
    str(r["motion_pattern"]): r["direction"]
    for r in motion
    if r.get("motion_pattern") in {"1", "2", "3", "4"}
}
bindings_by_key = collections.defaultdict(list)
for r in bindings:
    bindings_by_key[(r["config_id"], r["record_id"], r["selector_hex"])].append(r)
spawn_by_key = {
    (r["config_id"], r["record_id"], r["selector_hex"]): r for r in spawn_rows
}

out = []
for actor in actors:
    key = (actor["config_id"], actor["record_id"], actor["selector_hex"])
    linked = bindings_by_key.get(key, [])
    valid = [r for r in linked if r.get("binding_status") in VALID_BINDING_STATUSES]
    decoded = [r for r in valid if r.get("decoded_text")]
    frame = frame_by_record.get(actor["record_id"], {})
    visual = visual_by_selector.get(actor["selector_hex"], {})
    semantic = semantic_by_key.get(key, {})
    spawn = spawn_by_key.get(key, {})

    cfg_confirmed = any(
        r.get("binding_status") == "actor_to_event_dialogue_static_cfg"
        and r.get("confidence") == "confirmed_static"
        for r in decoded
    )
    if cfg_confirmed:
        behavior_class = "dialogue_actor_confirmed_cfg"
        behavior_confidence = "confirmed_static"
    elif decoded:
        behavior_class = "dialogue_actor_strong_candidate"
        behavior_confidence = "strong_candidate"
    elif valid:
        behavior_class = "event_source_bound_actor"
        behavior_confidence = "strong_structural"
    else:
        behavior_class = "placed_actor_no_validated_source"
        behavior_confidence = "placement_only"

    facing_seed = str(actor.get("field_06D9_seed") or "")
    facing = facing_by_pattern.get(facing_seed, "")
    pointer_match = bool(frame) and actor["controller_pointer"] == frame.get("trailer_start")

    evidence = [
        "controller pointer equals structural event trailer"
        if pointer_match else "controller pointer not independently matched",
        f"{len(valid)} validated event source binding(s)"
        if valid else "no validated source selection",
    ]
    if decoded:
        evidence.append(f"{len(decoded)} decoded dialogue source(s)")
    if facing:
        evidence.append(
            f"field06D9={facing_seed} matches confirmed motion-pattern value {facing}; "
            "reader linkage not yet proven"
        )

    body_bytes = [x for x in (actor.get("body_hex") or "").split() if x]
    actor_offset = int(actor.get("actor_command_offset") or 0)
    prefix_size = actor_offset
    suffix_size = max(0, len(body_bytes) - actor_offset - 6)
    if actor.get("binding_evidence") == "static_event_head_opcode59_actor_controller":
        record_body_shape = (
            "head_exact_placement_only" if len(body_bytes) == 6
            else "head_placement_plus_suffix"
        )
    elif actor.get("binding_evidence") == "static_event_tail_opcode59_actor_controller":
        record_body_shape = "prefix_plus_tail_placement"
    else:
        record_body_shape = "other_or_unresolved"

    flag_seed = actor.get("field_0719_seed") or ""
    out.append({
        "config_id": actor["config_id"],
        "pack_id_hex": actor["pack_id_hex"],
        "record_id": actor["record_id"],
        "selector_hex": actor["selector_hex"],
        "visual_form": visual.get("visual_form", ""),
        "semantic_role": semantic.get("semantic_role", "unknown"),
        "controller_pointer": actor["controller_pointer"],
        "controller_pointer_status": (
            "confirmed_frame_trailer_pointer" if pointer_match else "unresolved_or_mismatch"
        ),
        "controller_dispatch_grammar": frame.get("trailer_grammar", ""),
        "controller_dispatch_keys": (
            "0x7A->body16;0x7C->next_record_plus_1_16;0x00->terminator"
            if frame.get("trailer_grammar") else ""
        ),
        "actor_command_position": actor.get("binding_evidence", ""),
        "record_body_shape": record_body_shape,
        "record_body_size": len(body_bytes),
        "actor_command_offset": actor_offset,
        "body_prefix_size": prefix_size,
        "body_suffix_size": suffix_size,
        "body_suffix_hex": " ".join(body_bytes[actor_offset + 6:]),
        "spawn_condition_status": spawn.get("condition_status", ""),
        "spawn_condition_expr": spawn.get("condition_expr", ""),
        "spawn_visibility_when_state_unknown": spawn.get("visibility_when_state_unknown", ""),
        "field_06D9_seed": facing_seed,
        "initial_facing_candidate": facing,
        "initial_facing_status": (
            "candidate_value_domain_matches_confirmed_motion_pattern" if facing else "unresolved"
        ),
        "field_0719_seed_dec": flag_seed,
        "field_0719_seed_hex": (
            f"0x{int(flag_seed):02X}" if flag_seed != "" else ""
        ),
        "validated_event_source_count": len(valid),
        "decoded_dialogue_source_count": len(decoded),
        "behavior_class": behavior_class,
        "behavior_confidence": behavior_confidence,
        "evidence": "; ".join(evidence),
        "provenance": (
            "static_map_actor_selector_crosslink_20260930.csv;"
            "event_record_frame_catalog.csv;"
            "static_actor_event_dialogue_binding_20260930.csv;"
            "actor_motion_direction_pattern_table_20260930.csv"
        ),
    })

catalog_path = NPC / "static_actor_behavior_catalog_20260930.csv"
with catalog_path.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

class_counts = collections.Counter(r["behavior_class"] for r in out)
body_shape_counts = collections.Counter(r["record_body_shape"] for r in out)
spawn_status_counts = collections.Counter(r["spawn_condition_status"] for r in out)
facing_counts = collections.Counter(r["initial_facing_candidate"] for r in out)
flag_counts = collections.Counter(r["field_0719_seed_hex"] for r in out)
pointer_matches = sum(
    r["controller_pointer_status"] == "confirmed_frame_trailer_pointer" for r in out
)

rank = {
    "placed_actor_no_validated_source": 0,
    "event_source_bound_actor": 1,
    "dialogue_actor_strong_candidate": 2,
    "dialogue_actor_confirmed_cfg": 3,
}
record_class = {}
for r in out:
    key = (r["pack_id_hex"], r["record_id"])
    current = record_class.get(key)
    if current is None or rank[r["behavior_class"]] > rank[current]:
        record_class[key] = r["behavior_class"]

summary = {
    "schema_version": 1,
    "actor_rows": len(out),
    "unique_actor_records": len(record_class),
    "controller_pointer_matches_event_trailer": pointer_matches,
    "controller_pointer_mismatches": len(out) - pointer_matches,
    "actor_behavior_class_counts": dict(class_counts),
    "record_body_shape_counts": dict(body_shape_counts),
    "spawn_condition_status_counts": dict(spawn_status_counts),
    "unique_record_behavior_class_counts": dict(collections.Counter(record_class.values())),
    "initial_facing_candidate_counts": dict(facing_counts),
    "field_0719_seed_counts": dict(flag_counts),
    "source_bound_actor_rows": sum(
        class_counts[x]
        for x in (
            "event_source_bound_actor",
            "dialogue_actor_strong_candidate",
            "dialogue_actor_confirmed_cfg",
        )
    ),
    "decoded_dialogue_actor_rows": (
        class_counts["dialogue_actor_strong_candidate"]
        + class_counts["dialogue_actor_confirmed_cfg"]
    ),
    "field06d9_evidence_catalog": "data/npc_display/field06d9_direction_evidence_20260930.csv",
    "field06d9_evidence_summary": "data/npc_display/field06d9_direction_evidence_summary_20260930.json",
    "initial_facing_runtime_corroboration": {
        "field_value": 2,
        "direction": "down/front",
        "selector_families": ["0x24", "0x59", "0x40"],
        "runtime_frames": [240, 35, 11],
        "status": "confirmed_runtime_visual_support_but_direct_reader_unresolved",
    },
    "initial_facing_scope": (
        "strong candidate only: field06D9 exactly uses motion-pattern values 1..4; "
        "pack 0x50 independently corroborates value 2 as front in three selector families; "
        "a non-opcode59 C0 handler uses the same shared SoA column as a script cursor, "
        "so direct opcode59-handler reader linkage is still required"
    ),
    "field0719_scope": "raw controller seed/flags only; semantics unresolved",
}
(NPC / "static_actor_behavior_summary_20260930.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

viewer_rows = []
for r in out:
    viewer_rows.append({
        "config_id": r["config_id"],
        "record_id": r["record_id"],
        "selector_hex": r["selector_hex"],
        "behavior": {
            "behavior_class": r["behavior_class"],
            "behavior_confidence": r["behavior_confidence"],
            "controller_pointer": r["controller_pointer"],
            "controller_pointer_status": r["controller_pointer_status"],
            "controller_dispatch_grammar": r["controller_dispatch_grammar"],
            "record_body_shape": r["record_body_shape"],
            "record_body_size": int(r["record_body_size"]),
            "body_prefix_size": int(r["body_prefix_size"]),
            "body_suffix_size": int(r["body_suffix_size"]),
            "body_suffix_hex": r["body_suffix_hex"] or None,
            "spawn_condition_status": r["spawn_condition_status"] or None,
            "spawn_condition_expr": r["spawn_condition_expr"] or None,
            "spawn_visibility_when_state_unknown": r["spawn_visibility_when_state_unknown"] or None,
            "initial_facing_candidate": r["initial_facing_candidate"] or None,
            "initial_facing_status": r["initial_facing_status"],
            "field_0719_seed_hex": r["field_0719_seed_hex"] or None,
            "validated_event_source_count": int(r["validated_event_source_count"]),
            "decoded_dialogue_source_count": int(r["decoded_dialogue_source_count"]),
            "evidence": r["evidence"],
            "provenance": r["provenance"],
        },
    })

(VIEWER / "actor_behavior.json").write_text(
    json.dumps(
        {
            "schema_version": 1,
            "purpose": "controller/event behavior evidence overlay for static actors",
            "actor_behavior": viewer_rows,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print(json.dumps(summary, ensure_ascii=False, indent=2))
