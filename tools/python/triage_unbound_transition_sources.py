#!/usr/bin/env python3
"""Reproducible triage of source-unbound transitions, without inventing map links.

A unique script-pack -> map-config crosslink is ONLY an investigative lead:
the script pack may be a callable context and not the current player map.
No candidate source_config_id is modified.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORLD=ROOT/"viewer/data/world.json"
OWNER=ROOT/"data/maps/context/map_dialogue_pack_crosslink.csv"
OUTPUT=ROOT/"data/maps/transitions/source_unbound_investigation_queue.json"


def load_csv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def queue(world:dict, owner_rows:list[dict]) -> dict:
    owners=defaultdict(set)
    for r in owner_rows:
        pack=(r.get("pack_id_hex") or "").strip().upper()
        cfg=(r.get("config_id") or "").strip()
        if pack and cfg:
            owners[pack].add(cfg)
    unbound=[x for x in world["transition_candidates"] if not x.get("source_config_id")]
    groups=defaultdict(list)
    for c in unbound:
        pack=(c.get("script_pack") or "").strip().upper()
        groups[(c.get("trigger_type") or "unknown",pack)].append(c)
    category_counts=Counter()
    detailed=[]
    for (trigger,pack),records in groups.items():
        candidates=sorted(owners.get(pack,set()))
        if not pack:
            category="missing_script_pack"
        elif len(candidates)==1:
            category="one_pack_context_candidate_not_proof"
        elif len(candidates)>1:
            category="multiple_pack_context_candidates"
        else:
            category="no_map_context_in_current_index"
        category_counts[category]+=len(records)
        needs_research=(
            "Confirm event-record ownership, active pack/scene at trigger, and "
            "VM caller context in canonical ROM; never use pack equality alone."
        )
        detailed.append({
            "script_pack":pack or None,
            "trigger_type":trigger,
            "candidate_count":len(records),
            "context_config_candidates":candidates[:20],
            "context_config_total":len(candidates),
            "context_class":category,
            "sample_transition_ids":[x["transition_id"] for x in records[:8]],
            "next_proof":needs_research,
        })
    detailed.sort(key=lambda x:(-x["candidate_count"],x["trigger_type"],x["script_pack"] or ""))
    types=Counter(x.get("trigger_type") or "unknown" for x in unbound)
    return {
        "schema_version":1,
        "kind":"source_unbound_transition_triage",
        "source_unbound_after_overlay":len(unbound),
        "raw_catalog_vs_viewer_note":"Canonical candidate CSV may have more source-null rows; viewer includes proven hotspot overlays.",
        "source_unbound_trigger_type_counts":dict(sorted(types.items(),key=lambda kv:(-kv[1],kv[0]))),
        "pack_context_class_counts":dict(sorted(category_counts.items())),
        "group_count":len(detailed),
        "top_groups":detailed[:80],
        "policy":"Diagnostic grouping only; no graph promotion and no source Config ID assignment by script-pack identity.",
        "next_evidence_focus":"Resolve the high-count VM opcode 0x56 families through event-script owner/caller context and native pack-state stack.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--world",type=Path,default=WORLD)
    p.add_argument("--owners",type=Path,default=OWNER)
    p.add_argument("--output",type=Path,default=OUTPUT)
    args=p.parse_args()
    result=queue(json.loads(args.world.read_text(encoding="utf-8")),load_csv(args.owners))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="top_groups"},ensure_ascii=False))


if __name__=="__main__":
    main()
