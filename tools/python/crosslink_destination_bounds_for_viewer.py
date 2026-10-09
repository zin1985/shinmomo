#!/usr/bin/env python3
"""Conservatively attach native-bounds-derived destination configurations to viewer candidates.

The input resolver CSV is pre-existing. Never modify the transition candidate CSV.
No config is promoted when an opcode address/pack/arrival coordinate is inconsistent.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/maps/transitions/map_transition_candidates.csv"
RESOLUTIONS = ROOT / "data/maps/transitions/destination_config_bounds_resolution.csv"
SUMMARY = ROOT / "data/maps/transitions/destination_bounds_viewer_overlay_summary.json"


def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def normalized(value: str | None) -> str:
    return (value or "").strip().upper()


def join_destination_bounds(candidates: list[dict[str,str]], resolutions: list[dict[str,str]]):
    """Return (new unique bindings by 0-based candidate index, audit entries)."""
    by_addr: dict[str,list[int]] = defaultdict(list)
    for i, row in enumerate(candidates):
        addr = normalized(row.get("trigger_addr"))
        if addr:
            by_addr[addr].append(i)
    bindings = {}
    audit = []
    duplicates = set()
    for evidence in resolutions:
        addr = normalized(evidence.get("trigger_addr"))
        matches = by_addr.get(addr, [])
        status = None
        index = matches[0] if len(matches) == 1 else None
        if len(matches) != 1:
            status = "ambiguous_or_missing_address"
        elif str(evidence.get("candidate_count", "")).strip() != "1":
            status = "not_unique_native_bounds"
        else:
            candidate = candidates[index]
            config_id = (evidence.get("resolved_config_id") or "").strip()
            match = (
                bool(config_id)
                and normalized(candidate.get("destination_pack")) == normalized(evidence.get("destination_pack"))
                and bool((candidate.get("destination_x") or "").strip())
                and bool((candidate.get("destination_y") or "").strip())
                and (candidate.get("destination_x") or "").strip() == (evidence.get("destination_x") or "").strip()
                and (candidate.get("destination_y") or "").strip() == (evidence.get("destination_y") or "").strip()
            )
            if not match:
                status = "pack_or_arrival_mismatch"
            elif candidate.get("destination_config_id") and candidate["destination_config_id"] != config_id:
                status = "existing_config_conflict"
            elif index in bindings or index in duplicates:
                status = "duplicate_resolution"
                duplicates.add(index)
                bindings.pop(index, None)
            elif candidate.get("destination_config_id"):
                status = "already_bound_consistent"
            else:
                bindings[index] = evidence
                status = "new_destination_binding"
        audit.append({"trigger_addr": addr, "candidate_row_index": index, "status": status,
                      "resolved_config_id": evidence.get("resolved_config_id") or ""})
    if duplicates:
        for a in audit:
            if a["candidate_row_index"] in duplicates and a["status"] == "new_destination_binding":
                a["status"] = "duplicate_resolution"
    return bindings, audit


def summary_for(candidates, resolutions, bindings, audit):
    counts = Counter(row["status"] for row in audit)
    return {
        "schema_version": 1,
        "source": str(RESOLUTIONS.relative_to(ROOT)).replace("\\","/"),
        "transition_candidates": len(candidates),
        "resolution_evidence_count": len(resolutions),
        "accepted_new_destination_config_bindings": len(bindings),
        "status_counts": dict(sorted(counts.items())),
        "unresolved_or_conflicting": [r for r in audit if r["status"] not in
            ("new_destination_binding","already_bound_consistent")],
        "policy": "Unique trigger_addr and candidate_count=1; destination pack and X/Y must agree exactly. No unverified expansion or single-config promotion of phase-dependent candidates.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates",type=Path,default=CANDIDATES)
    p.add_argument("--resolutions",type=Path,default=RESOLUTIONS)
    p.add_argument("--summary",type=Path,default=SUMMARY)
    args=p.parse_args()
    candidates, resolutions=read_csv(args.candidates),read_csv(args.resolutions)
    bindings,audit=join_destination_bounds(candidates,resolutions)
    result=summary_for(candidates,resolutions,bindings,audit)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=="__main__":
    main()
