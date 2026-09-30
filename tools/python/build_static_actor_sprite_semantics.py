#!/usr/bin/env python3
from pathlib import Path
import csv, collections, json

ROOT = Path(__file__).resolve().parents[2]
NPC = ROOT / "data/npc_display"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

actors = read_csv(NPC / "static_map_actor_selector_crosslink_20260930.csv")
visual_rows = read_csv(NPC / "static_map_bound_selector_visual_form_20260930.csv")
bindings = read_csv(NPC / "static_actor_event_dialogue_binding_20260930.csv")

visual_by_selector = {r["selector_hex"]: r for r in visual_rows}
dialogue_by_key = collections.defaultdict(list)
for r in bindings:
    dialogue_by_key[(r["config_id"], r["record_id"], r["selector_hex"])].append(r)

out = []
for actor in actors:
    key = (actor["config_id"], actor["record_id"], actor["selector_hex"])
    visual = visual_by_selector.get(actor["selector_hex"], {})
    decoded = [x for x in dialogue_by_key.get(key, []) if x.get("decoded_text")]
    form, detail = visual.get("visual_form", ""), visual.get("visual_detail", "")

    role, confidence, evidence = "unknown", "unknown", "no semantic evidence joined"

    if form == "animal_like":
        role, confidence = "animal", "high"
        evidence = f"visual classification={form}; {detail}; static opcode59 map binding"
    elif form == "object_like":
        role, confidence = "effect", "candidate"
        evidence = f"object-like static actor; {detail}; gameplay role not yet proven"
    elif form == "plant_or_effect_like":
        role, confidence = "effect", "candidate"
        evidence = f"plant/effect-like static actor; {detail}; gameplay role not yet proven"
    elif form in ("monster_like", "small_creature_like"):
        confidence = "candidate"
        evidence = f"{form}; {detail}; enemy allegiance not proven"

    if decoded:
        role, confidence = "talking_npc", "strong_candidate"
        evidence = (
            f"actor-bound decoded dialogue source(s)={len(decoded)}; "
            f"speaker record={actor['record_id']}; visual={detail or form or 'unclassified'}; "
            "finer occupation/name intentionally not inferred from dialogue alone"
        )

    if actor["config_id"] == "cfg_t04_l008_v2" and actor["record_id"].startswith("F50-L") and decoded:
        role, confidence = "villager", "high"
        evidence = (
            f"旅立ちの村 opcode59 actor; actor-bound decoded dialogue source(s)={len(decoded)}; "
            f"speaker record={actor['record_id']}; visual={detail or form or 'unclassified'}; "
            "finer occupation/name intentionally not inferred from dialogue alone"
        )

    out.append({
        "config_id": actor["config_id"],
        "record_id": actor["record_id"],
        "selector_hex": actor["selector_hex"],
        "semantic_role": role,
        "character_name": "",
        "appearance_class": detail or form,
        "confidence": confidence,
        "evidence": evidence,
        "provenance": (
            "static_map_actor_selector_crosslink_20260930.csv;"
            "static_map_bound_selector_visual_form_20260930.csv;"
            "static_actor_event_dialogue_binding_20260930.csv"
        ),
    })

path = NPC / "static_actor_sprite_semantics_20260930.csv"
with path.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

viewer_rows = []
for r in out:
    if not r["appearance_class"] and r["semantic_role"] == "unknown" and r["confidence"] == "unknown":
        continue
    viewer_rows.append({
        "config_id": r["config_id"],
        "record_id": r["record_id"],
        "selector_hex": r["selector_hex"],
        "sprite_semantics": {
            "semantic_role": r["semantic_role"] or None,
            "character_name": r["character_name"] or None,
            "appearance_class": r["appearance_class"] or None,
            "confidence": r["confidence"] or None,
            "evidence": r["evidence"] or None,
            "provenance": r["provenance"] or None,
        },
    })

viewer_path = ROOT / "viewer/data/actor_semantics.json"
viewer_path.write_text(
    json.dumps(
        {
            "schema_version": 3,
            "purpose": "semantic and appearance overrides applied by viewer without regenerating world.json",
            "actor_overrides": viewer_rows,
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)

print("rows", len(out))
print("viewer_overrides", len(viewer_rows))
print("role_counts", dict(collections.Counter(r["semantic_role"] for r in out)))
print(
    "tabidachi",
    [
        (r["record_id"], r["selector_hex"], r["semantic_role"], r["confidence"])
        for r in out
        if r["config_id"] == "cfg_t04_l008_v2"
    ],
)
