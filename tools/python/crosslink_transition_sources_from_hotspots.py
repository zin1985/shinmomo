#!/usr/bin/env python3
"""Bind transition source maps only when an independently anchored hotspot has an exact opcode address.

This does NOT reclassify candidate transitions as runtime-confirmed. Raw transition CSV
stays untouched. All evidence, unmatched cases and contradictions are retained.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/maps/transitions/map_transition_candidates.csv"
HOTSPOTS = ROOT / "data/maps/transitions/source_transition_hotspots.csv"
OUTPUT = ROOT / "data/maps/transitions/source_hotspot_transition_bindings.csv"
SUMMARY = ROOT / "data/maps/transitions/source_hotspot_transition_bindings_summary.json"

FIELDNAMES = (
    "hotspot_id", "trigger_addr", "transition_row_index", "transition_id",
    "source_config_id", "source_grid_x", "source_grid_y", "source_width",
    "source_height", "hotspot_type", "hotspot_confidence",
    "destination_config_id", "destination_x", "destination_y",
    "binding_status", "evidence", "provenance"
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def normalized_addr(value: str | None) -> str:
    return (value or "").strip().upper()


def crosslink(candidates: list[dict[str, str]], hotspots: list[dict[str, str]]):
    indexed: dict[str, list[int]] = defaultdict(list)
    for index, candidate in enumerate(candidates):
        addr = normalized_addr(candidate.get("trigger_addr"))
        if addr:
            indexed[addr].append(index)
    result = []
    for hotspot in hotspots:
        address = normalized_addr(hotspot.get("trigger_addr"))
        matches = indexed.get(address, []) if address else []
        source = (hotspot.get("source_config_id") or "").strip()
        candidate = candidates[matches[0]] if len(matches) == 1 else None
        conflicts = []
        if candidate:
            for field in ("source_config_id", "destination_config_id", "destination_x", "destination_y", "event_record"):
                a = (candidate.get(field) or "").strip()
                b = (hotspot.get(field) or "").strip()
                if a and b and a != b:
                    conflicts.append(f"{field}:{a}!={b}")
        if len(matches) > 1:
            status = "ambiguous_trigger_address"
        elif len(matches) == 0:
            status = "unmatched_trigger_address"
        elif not source:
            status = "missing_hotspot_source"
        elif conflicts:
            status = "conflict:" + ";".join(conflicts)
        elif (candidate.get("source_config_id") or "").strip():
            status = "already_bound_consistent"
        else:
            status = "new_source_binding"
        index_text = str(matches[0]) if candidate else ""
        result.append({
            "hotspot_id": hotspot.get("hotspot_id") or "",
            "trigger_addr": address,
            "transition_row_index": index_text,
            "transition_id": f"catalog_transition_{matches[0]:04d}" if candidate else "",
            "source_config_id": source,
            "source_grid_x": hotspot.get("source_grid_x") or "",
            "source_grid_y": hotspot.get("source_grid_y") or "",
            "source_width": hotspot.get("source_width") or "",
            "source_height": hotspot.get("source_height") or "",
            "hotspot_type": hotspot.get("hotspot_type") or "",
            "hotspot_confidence": hotspot.get("confidence") or "",
            "destination_config_id": hotspot.get("destination_config_id") or "",
            "destination_x": hotspot.get("destination_x") or "",
            "destination_y": hotspot.get("destination_y") or "",
            "binding_status": status,
            "evidence": hotspot.get("evidence") or "",
            "provenance": "data/maps/transitions/source_transition_hotspots.csv;" + (hotspot.get("provenance") or ""),
        })
    # A single transition must never receive two different source bindings.
    grouped: dict[int, list[dict]] = defaultdict(list)
    for item in result:
        if item["binding_status"] == "new_source_binding":
            grouped[int(item["transition_row_index"])].append(item)
    for group in grouped.values():
        if len(group) > 1:
            for item in group:
                item["binding_status"] = "ambiguous_multiple_hotspots"
    return result


def summarize(records: list[dict], candidates: list[dict]):
    counts = Counter(record["binding_status"].split(":", 1)[0] for record in records)
    bound = [r for r in records if r["binding_status"] == "new_source_binding"]
    with_destination = sum(
        bool((candidates[int(r["transition_row_index"])].get("destination_config_id") or "").strip())
        for r in bound
    )
    return {
        "schema_version": 1,
        "kind": "source_hotspot_transition_exact_opcode_binding",
        "source_catalog_count": len(candidates),
        "hotspot_count": len(records),
        "status_counts": dict(sorted(counts.items())),
        "new_source_binding_count": len(bound),
        "new_navigable_edge_count": with_destination,
        "new_source_without_destination_count": len(bound) - with_destination,
        "non_matching_hotspot_ids": [r["hotspot_id"] for r in records if r["binding_status"] == "unmatched_trigger_address"],
        "conflicts": [r["hotspot_id"] for r in records if r["binding_status"].startswith("conflict:")],
        "policy": "Exact unique trigger_addr + nonconflicting source/destination coordinates. No inferred map from script pack. Retain original confidence (strong_candidate remains nonconfirmed).",
    }


def run(candidate_path=CANDIDATES, hotspot_path=HOTSPOTS, output=OUTPUT, summary_path=SUMMARY):
    candidates, hotspots = rows(Path(candidate_path)), rows(Path(hotspot_path))
    records = crosslink(candidates, hotspots)
    summary = summarize(records, candidates)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with Path(output).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    Path(summary_path).write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates", type=Path, default=CANDIDATES)
    p.add_argument("--hotspots", type=Path, default=HOTSPOTS)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--summary", type=Path, default=SUMMARY)
    args = p.parse_args()
    run(args.candidates, args.hotspots, args.output, args.summary)


if __name__ == "__main__":
    main()
