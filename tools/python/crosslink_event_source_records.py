#!/usr/bin/env python3
"""Crosslink structural event-record frames to validated source selections.

This tool intentionally reuses the canonical source-pair usage catalog rather
than rescanning raw A4-looking bytes. That preserves the source-reader
reachability filter and avoids reintroducing rejected false positives.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, Counter
from pathlib import Path


def cpu_to_file(cpu: str) -> int:
    bank_s, addr_s = cpu.split(":", 1)
    bank = int(bank_s, 16)
    addr = int(addr_s, 16)
    return ((bank - 0xC0) << 16) | addr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=Path, default=Path("data/events/event_record_frame_catalog.csv"))
    ap.add_argument("--source-usage", type=Path, default=Path("data/dialogue/source_pair_usage_catalog.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("data/events"))
    args = ap.parse_args()

    frames = []
    with args.frames.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            row["family_id"] = int(row["family_id"])
            row["start_off"] = cpu_to_file(row["record_start"])
            row["end_off"] = cpu_to_file(row["record_end_exclusive"])
            frames.append(row)

    by_family = defaultdict(list)
    for row in frames:
        by_family[row["family_id"]].append(row)
    for rows in by_family.values():
        rows.sort(key=lambda r: r["start_off"])

    out = []
    source_rows = 0
    validated_callsites = 0
    with args.source_usage.open(encoding="utf-8-sig", newline="") as f:
        for src in csv.DictReader(f):
            if "high_conf_static_A4" not in src["evidence_classes"]:
                continue
            source_rows += 1
            family = int(src["family_id"])
            subindex = int(src["subindex"])
            cpus = [x for x in src["script_cpus"].split(";") if x]
            validated_callsites += len(cpus)
            for cpu in cpus:
                off = cpu_to_file(cpu)
                frame = next((r for r in by_family.get(family, [])
                              if r["start_off"] <= off < r["end_off"]), None)
                if frame is None:
                    continue
                out.append({
                    "record_id": frame["record_id"],
                    "family_id": family,
                    "family_hex": f"0x{family:02X}",
                    "record_start": frame["record_start"],
                    "record_end_exclusive": frame["record_end_exclusive"],
                    "subindex": subindex,
                    "subindex_hex": f"0x{subindex:02X}",
                    "script_callsite": cpu,
                    "patterns": src["patterns"],
                    "selected_source_cpu": src["selected_source_cpu"],
                    "player_visible": src["player_visible"],
                    "evidence_class": "validated_source_selection_in_structural_record",
                })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "event_source_crosslink.csv"
    if out:
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)

    counts = Counter(r["record_id"] for r in out)
    summary = {
        "structural_record_count": len(frames),
        "structural_record_families": len({r["family_id"] for r in frames}),
        "validated_high_conf_source_pairs_considered": source_rows,
        "validated_script_callsites_considered": validated_callsites,
        "mapped_source_callsites": len(out),
        "records_with_mapped_source": len(counts),
        "families_with_mapped_source": len({r["family_id"] for r in out}),
        "unmapped_validated_script_callsites": validated_callsites - len(out),
        "records_without_mapped_source": len(frames) - len(counts),
        "mapped_sources_per_record": {str(k): v for k, v in sorted(Counter(counts.values()).items())},
        "interpretation": "structural event framing is now directly linked to already-validated source selections; semantic event meaning and runtime reachability remain separate",
    }
    (args.out_dir / "event_source_crosslink_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
