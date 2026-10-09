#!/usr/bin/env python3
"""Audit event-aware world connectivity without inventing missing map edges.

Uses derived viewer JSON only. A one-way edge can be a legitimate event:
report it as requiring inspection, not as a proven error.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORLD=ROOT/"viewer/data/world.json"
OUT=ROOT/"data/maps/transitions/world_graph_coverage_summary.json"


def audit(world: dict) -> dict:
    maps={m["config_id"] for m in world["maps"]}
    edges=world["transition_edges"]
    candidates=world["transition_candidates"]
    outgoing: dict[str,set[str]]=defaultdict(set)
    incoming: dict[str,set[str]]=defaultdict(set)
    undirected: dict[str,set[str]]=defaultdict(set)
    for e in edges:
        a,b=e.get("source_config_id"),e.get("destination_config_id")
        if not a or not b or a not in maps or b not in maps:
            continue
        outgoing[a].add(b)
        incoming[b].add(a)
        undirected[a].add(b)
        undirected[b].add(a)
    unseen=set(maps)
    components=[]
    while unseen:
        start=min(unseen)
        group={start}
        queue=deque([start])
        unseen.remove(start)
        while queue:
            for neighbor in sorted(undirected.get(queue.popleft(),set())):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    group.add(neighbor)
                    queue.append(neighbor)
        components.append(sorted(group))
    components.sort(key=lambda c:(-len(c),c[0]))
    pairs={(a,b) for a,bs in outgoing.items() for b in bs}
    one_way=sorted((a,b) for a,b in pairs if a!=b and (b,a) not in pairs)
    unresolved_src=Counter(
        e.get("destination_config_id") for e in candidates
        if not e.get("source_config_id") and e.get("destination_config_id")
    )
    return {
        "schema_version":1,
        "kind":"event_aware_map_graph_coverage_audit",
        "map_count":len(maps),
        "catalog_candidate_count":len(candidates),
        "bound_edge_count":len(edges),
        "confirmed_runtime_edge_count":sum(e.get("confidence")=="confirmed" for e in edges),
        "candidate_bound_edge_count":sum(e.get("confidence")!="confirmed" for e in edges),
        "native_boundary_context_count":sum(bool(e.get("native_boundary_context")) for e in edges),
        "edges_with_unknown_current_activation":sum(e.get("activation_gate",{}).get("evaluation")=="unknown" for e in edges),
        "maps_with_at_least_one_outgoing":sum(bool(outgoing.get(m)) for m in maps),
        "maps_with_at_least_one_incoming":sum(bool(incoming.get(m)) for m in maps),
        "maps_with_no_bound_outgoing":sorted(m for m in maps if not outgoing.get(m)),
        "maps_with_no_bound_incoming":sorted(m for m in maps if not incoming.get(m)),
        "weak_component_count":len(components),
        "largest_weak_component_map_count":len(components[0]) if components else 0,
        "weak_component_sizes":[len(group) for group in components],
        "one_way_map_pair_candidates":[{"source":a,"destination":b} for a,b in one_way],
        "one_way_pair_count":len(one_way),
        "top_unbound_destination_configs":[{"config_id":k,"unbound_candidate_count":v}
            for k,v in sorted(unresolved_src.items(),key=lambda x:(-x[1],x[0]))[:20]],
        "unknown_source_candidates":sum(not e.get("source_config_id") for e in candidates),
        "unknown_destination_candidates":sum(not e.get("destination_config_id") for e in candidates),
        "interpretation":"Incomplete connectivity is a research backlog; one-way links are not proven bugs. Current story-state gate unknown means preview-only, not executable navigation.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,default=WORLD)
    p.add_argument("--output",type=Path,default=OUT)
    args=p.parse_args()
    result=audit(json.loads(args.world.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if not isinstance(v,list)},ensure_ascii=False))


if __name__=="__main__":
    main()
