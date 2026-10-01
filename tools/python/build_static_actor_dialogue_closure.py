#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEQ = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
SPAWN = ROOT / "data/npc_display/static_actor_spawn_conditions_20260930.csv"
OUT_JSON = ROOT / "data/npc_display/static_actor_dialogue_closure_20261002.json"
OUT_CSV = ROOT / "data/npc_display/static_actor_dialogue_closure_20261002.csv"

REFERENCE_CONFIG = "cfg_t04_l008_v2"
REFERENCE_RECORD = "F50-L004"
EXPANSION_PACK = "0x50"


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def closure_checks(actor: dict, spawn: dict | None) -> dict[str, bool]:
    seqs = actor.get("dialogue_sequences", [])
    pages = [p for s in seqs for p in s.get("pages", [])]
    spawn_status = (spawn or {}).get("condition_status", "")
    spawn_expr = (spawn or {}).get("condition_expr", "")
    return {
        "scene_key_present": bool(actor.get("scene_id") and actor.get("pack_id_hex")),
        "actor_identity_present": bool(
            actor.get("record_id") and actor.get("selector_hex") and actor.get("controller_pointer")
        ),
        "spawn_resolved": spawn_status.startswith("confirmed_static"),
        "spawn_expression_resolved": bool(spawn_expr),
        "has_dialogue_variants": bool(seqs),
        "all_sources_direct_decoded": bool(seqs) and all(
            s.get("source", {}).get("decode_status") == "confirmed_static_direct_decode"
            for s in seqs
        ),
        "all_sources_zero_unknown_tokens": bool(seqs) and all(
            s.get("source", {}).get("decoder_unknown_tokens") == 0
            for s in seqs
        ),
        "all_conditions_cfg_resolved": bool(seqs) and all(
            s.get("condition", {}).get("status") in {
                "confirmed_static_cfg",
                "confirmed_static_single_path",
            }
            for s in seqs
        ),
        "all_variants_accounted_for": bool(seqs) and all(
            s.get("condition", {}).get("source_variant_count") == len(seqs)
            for s in seqs
        ),
        "all_pages_present": bool(seqs) and all(bool(s.get("pages")) for s in seqs),
        "all_page_boundaries_family50_confirmed": bool(pages) and all(
            p.get("page_boundary", {}).get("status", "").startswith("confirmed_static_family50")
            for p in pages
        ),
        "all_text_records_terminate_00": bool(seqs) and all(
            s.get("termination", {}).get("text_record_end") == "0x00"
            and s.get("termination", {}).get("text_record_end_status") == "confirmed_static"
            for s in seqs
        ),
    }


def branch_rows(actor: dict) -> list[dict]:
    rows = []
    for s in actor.get("dialogue_sequences", []):
        pages = s.get("pages", [])
        rows.append({
            "variant_order": s.get("variant_order"),
            "sequence_id": s.get("sequence_id"),
            "event_record": s.get("event", {}).get("record_id"),
            "controller_pointer": s.get("event", {}).get("controller_pointer"),
            "dialogue_command_addr": s.get("event", {}).get("dialogue_command_addr"),
            "condition_id": s.get("condition", {}).get("condition_id"),
            "condition_status": s.get("condition", {}).get("status"),
            "condition_expr": s.get("condition", {}).get("expression"),
            "branch_path": s.get("condition", {}).get("branch_path"),
            "text_record_id": s.get("source", {}).get("text_record_id"),
            "text_pointer": s.get("source", {}).get("text_pointer"),
            "decode_status": s.get("source", {}).get("decode_status"),
            "decoder_unknown_tokens": s.get("source", {}).get("decoder_unknown_tokens"),
            "page_count": len(pages),
            "page_boundaries": [
                p.get("page_boundary", {}).get("status") for p in pages
            ],
            "termination": s.get("termination", {}),
        })
    return rows


def main() -> None:
    obj = json.loads(SEQ.read_text(encoding="utf-8"))
    spawn_rows = read_csv(SPAWN)
    spawn_by_key = {
        (r.get("config_id", ""), r.get("record_id", "")): r
        for r in spawn_rows
    }

    family50 = [a for a in obj["actors"] if a.get("pack_id_hex") == EXPANSION_PACK]
    expansion = []
    for actor in family50:
        key = (actor.get("config_id", ""), actor.get("record_id", ""))
        spawn = spawn_by_key.get(key)
        checks = closure_checks(actor, spawn)
        failed = [name for name, ok in checks.items() if not ok]
        expansion.append({
            "scene_id": actor.get("scene_id"),
            "pack_id_hex": actor.get("pack_id_hex"),
            "config_id": actor.get("config_id"),
            "record_id": actor.get("record_id"),
            "selector_hex": actor.get("selector_hex"),
            "closure_status": "closed_static_to_page" if not failed else "incomplete",
            "failed_checks": failed,
            "variant_count": len(actor.get("dialogue_sequences", [])),
            "page_count": sum(len(s.get("pages", [])) for s in actor.get("dialogue_sequences", [])),
            "spawn_condition_status": (spawn or {}).get("condition_status"),
            "spawn_condition_expr": (spawn or {}).get("condition_expr"),
        })

    actor = next(
        a for a in family50
        if a.get("config_id") == REFERENCE_CONFIG
        and a.get("record_id") == REFERENCE_RECORD
    )
    spawn = spawn_by_key[(REFERENCE_CONFIG, REFERENCE_RECORD)]
    checks = closure_checks(actor, spawn)
    branches = branch_rows(actor)
    closed = all(checks.values())

    result = {
        "schema_version": "2026-10-02-dialogue-closure-v2",
        "scope": "scene_actor_spawn_event_condition_dialogue_sequence_page",
        "reference_actor": {
            "scene_id": actor.get("scene_id"),
            "pack_id_hex": actor.get("pack_id_hex"),
            "config_id": actor.get("config_id"),
            "record_id": actor.get("record_id"),
            "selector_hex": actor.get("selector_hex"),
            "controller_pointer": actor.get("controller_pointer"),
            "spawn": {
                "condition_status": spawn.get("condition_status"),
                "condition_expr": spawn.get("condition_expr"),
                "state_evaluation": spawn.get("state_evaluation"),
                "visibility_when_state_unknown": spawn.get("visibility_when_state_unknown"),
            },
            "variant_count": len(actor.get("dialogue_sequences", [])),
            "page_count": sum(len(s.get("pages", [])) for s in actor.get("dialogue_sequences", [])),
            "branches": branches,
        },
        "closure": {
            "status": "closed_static_to_page" if closed else "incomplete",
            "checks": checks,
            "unresolved_out_of_scope": [
                "exact_in_game_place_name",
                "speaker_semantic_identity",
                "relation_key_0x90_gameplay_label",
                "event_continuation_after_text_record",
            ],
        },
        "mechanical_expansion": {
            "pack_id_hex": EXPANSION_PACK,
            "actor_count": len(expansion),
            "closed_actor_count": sum(x["closure_status"] == "closed_static_to_page" for x in expansion),
            "closed_actor_ids": [
                x["record_id"] for x in expansion
                if x["closure_status"] == "closed_static_to_page"
            ],
            "actors": expansion,
        },
        "evidence_sources": [
            "data/npc_display/static_actor_dialogue_sequences_20260930.json",
            "data/npc_display/static_actor_spawn_conditions_20260930.csv",
            "data/npc_display/static_actor_dialogue_conditions_20260930.csv",
            "data/npc_display/static_actor_event_dialogue_binding_20260930.csv",
            "data/dialogue/family50_canonical_direct_decode_20260930.csv",
            "docs/analysis/family50_dialogue_condition_cfg_20260930.md",
            "docs/analysis/family50_location_label_correction_20260930.md",
        ],
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_rows = []
    for row in expansion:
        csv_rows.append({
            "scene_id": row["scene_id"],
            "pack_id_hex": row["pack_id_hex"],
            "config_id": row["config_id"],
            "record_id": row["record_id"],
            "selector_hex": row["selector_hex"],
            "closure_status": row["closure_status"],
            "failed_checks": ";".join(row["failed_checks"]),
            "variant_count": row["variant_count"],
            "page_count": row["page_count"],
            "spawn_condition_status": row["spawn_condition_status"],
            "spawn_condition_expr": row["spawn_condition_expr"],
            "is_reference_actor": int(row["record_id"] == REFERENCE_RECORD and row["config_id"] == REFERENCE_CONFIG),
        })
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)

    print(json.dumps({
        "reference_actor": REFERENCE_RECORD,
        "closure_status": result["closure"]["status"],
        "variant_count": result["reference_actor"]["variant_count"],
        "page_count": result["reference_actor"]["page_count"],
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "family50_actor_count": len(expansion),
        "family50_closed_actor_count": result["mechanical_expansion"]["closed_actor_count"],
        "family50_closed_actor_ids": result["mechanical_expansion"]["closed_actor_ids"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
