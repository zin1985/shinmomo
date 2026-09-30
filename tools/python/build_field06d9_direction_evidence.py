#!/usr/bin/env python3
from pathlib import Path
import csv, json, collections

ROOT = Path(__file__).resolve().parents[2]
NPC = ROOT / "data/npc_display"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

actors = read_csv(NPC / "static_map_actor_selector_crosslink_20260930.csv")
directional = {
    r["selector_hex"]: r
    for r in read_csv(NPC / "static_character_directional_catalog_20260930.csv")
}
motion = {
    str(r["motion_pattern"]): r["direction"]
    for r in read_csv(NPC / "actor_motion_direction_pattern_table_20260930.csv")
    if str(r.get("motion_pattern")) in {"1", "2", "3", "4"}
}

counts = collections.Counter(str(r["field_06D9_seed"]) for r in actors)
pack50 = [r for r in actors if r["pack_id_hex"] == "0x50"]

runtime_cases = [
    ("0x24", 2, 240, ["F50-L002"]),
    ("0x59", 3, 35, ["F50-L003", "F50-L004"]),
    ("0x40", 3, 11, ["F50-L001", "F50-L006"]),
]
runtime_rows = []
for selector, group, frame, record_ids in runtime_cases:
    d = directional[selector]
    front = [int(x) for x in d["front_frames"].split(",") if x]
    matched = [
        r for r in pack50
        if r["selector_hex"] == selector and r["record_id"] in record_ids
    ]
    if not matched or any(str(r["field_06D9_seed"]) != "2" for r in matched):
        raise RuntimeError(f"pack50 field06D9 evidence changed for {selector}")
    if frame not in front:
        raise RuntimeError(f"runtime frame {frame} no longer front for {selector}")
    runtime_rows.append({
        "selector_hex": selector,
        "field_value": 2,
        "runtime_group": group,
        "runtime_frame": frame,
        "confirmed_front_frames": front,
        "record_ids": record_ids,
    })

summary = {
    "schema_version": 1,
    "field": "$06D9,X",
    "opcode59_actor_rows": len(actors),
    "value_counts": dict(sorted(counts.items())),
    "candidate_direction_mapping": motion,
    "runtime_front_corroboration": runtime_rows,
    "shared_soa_counterexample": {
        "scope": "non-opcode59 C0 handler",
        "addresses": ["C0:BAEA", "C0:BB33", "C0:BB4D"],
        "interpretation": "script/table cursor or index",
        "significance": "$06D9 column semantics are handler-local, not globally direction",
    },
    "conclusion_status": "strong_candidate_not_confirmed",
    "conclusion": (
        "For the opcode59 actor path, field06D9 strongly matches an initial-facing/direction "
        "seed and value 2 is runtime-corroborated as front in three selector families. "
        "Direct opcode59-handler reader linkage remains missing."
    ),
}
(NPC / "field06d9_direction_evidence_summary_20260930.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))
