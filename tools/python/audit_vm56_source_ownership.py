#!/usr/bin/env python3
"""Evidence-focused audit of VM opcode 0x56 source ownership.

Verifies terminal opcode operands against canonical ROM when explicitly supplied.
Event record and selected-source links are evidence of a *script callsite*,
not proof of the player map. This tool NEVER mutates source_config_id.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/maps/transitions/map_transition_candidates.csv"
FRAMES = ROOT / "data/events/event_record_frame_catalog.csv"
XREF = ROOT / "data/events/event_source_crosslink.csv"
OUT = ROOT / "data/maps/transitions/vm56_source_ownership_audit.json"
EXPECTED_SHA = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
EXPECTED_SIZE = 2097152


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def file_offset(addr: str) -> int:
    bank, low = addr.split(":")
    b, a = int(bank, 16), int(low, 16)
    if not (0xC0 <= b <= 0xFF and 0 <= a <= 0xFFFF):
        raise ValueError(f"Unsupported ROM CPU address {addr}")
    off = ((b - 0xC0) << 16) | a
    if off >= EXPECTED_SIZE:
        raise ValueError(f"ROM offset out of range for {addr}")
    return off


def audit(candidates, frame_rows, xrefs, rom: bytes | None = None, derived=None):
    rows56 = [r for r in candidates if r.get("trigger_type") == "vm_opcode_0x56_terminal"]
    known_frame_by_id = {r["record_id"]: r for r in frame_rows}
    xrefs_by_record = defaultdict(list)
    for x in xrefs:
        xrefs_by_record[x["record_id"]].append(x)
    view_source_by_addr = {
        (r.get("trigger_addr") or "").upper():r.get("source_config_id")
        for r in (derived or [])
        if r.get("source_config_id") and r.get("trigger_addr")
    }
    issues, ready, counts = [], [], Counter()
    byte_audits = 0
    for r in rows56:
        addr = r["trigger_addr"]
        src = r.get("source_config_id") or view_source_by_addr.get(addr.upper())
        record_id = r.get("event_record") or ""
        linked = xrefs_by_record.get(record_id, []) if record_id else []
        if record_id and record_id not in known_frame_by_id:
            issues.append({"addr":addr, "error":"event_record_missing_in_frame_catalog"})
        if record_id:
            frame=known_frame_by_id.get(record_id)
            if frame and not (file_offset(frame["record_start"]) <= file_offset(addr) < file_offset(frame["record_end_exclusive"])):
                issues.append({"addr":addr,"error":"trigger_outside_declared_record"})
        dest_pack = int(r["destination_pack"],16)
        dest_entry = int(r["destination_entry_id"],16)
        if rom is not None:
            off=file_offset(addr)
            if off+4>len(rom) or list(rom[off:off+4]) != [0x56,dest_pack,dest_entry,0xB0]:
                issues.append({"addr":addr,"error":"ROM_opcode_tail_mismatch"})
            else:
                byte_audits+=1
        counts["terminal_0x56_total"]+=1
        counts["source_bound_in_viewer"]+=bool(src)
        counts["source_unbound_in_viewer"]+=not bool(src)
        counts["within_structural_event_frame"]+=bool(record_id)
        counts["frame_plus_source_selection"]+=bool(linked)
        counts["no_event_frame"]+=not bool(record_id)
        counts["frame_without_source_selection"]+=bool(record_id) and not bool(linked)
        if record_id:
            priority=0 if linked else 1
            ready.append({
                "priority":priority,
                "trigger_addr":addr,
                "script_pack":r["script_pack"],
                "script_record":r["script_record"],
                "script_entry":r["script_entry"],
                "event_record":record_id,
                "validated_source_selection_count":len(linked),
                "validated_script_callsites":[{
                    "script_callsite":x["script_callsite"],
                    "source_selection_relative_to_transition": (
                        "before_in_rom_address_order" if file_offset(x["script_callsite"]) < file_offset(addr)
                        else "after_in_rom_address_order" if file_offset(x["script_callsite"]) > file_offset(addr)
                        else "same_address_unexpected"
                    ),
                    "source_selection_pattern":x.get("patterns") or "",
                    "is_proven_vm_caller":False,
                    "selected_source_cpu":x["selected_source_cpu"],
                    "source_selection_subindex":x["subindex_hex"],
                    "evidence_class":x["evidence_class"]
                } for x in linked],
                "destination_pack":r["destination_pack"],
                "destination_entry_id":r["destination_entry_id"],
                "destination_config_id":r["destination_config_id"] or None,
                "viewer_source_config_id":src or None,
                "remaining_proof":"Trace callsite selection to active map pack/config and confirm VM normal mode and triggering predicate; do not infer source from script pack."
            })
    ready.sort(key=lambda r:(r["priority"],-r["validated_source_selection_count"],r["trigger_addr"]))
    if rom is not None and (len(rom)!=EXPECTED_SIZE or hashlib.sha256(rom).hexdigest().upper()!=EXPECTED_SHA):
        raise ValueError("Canonical ROM identity mismatch")
    report={
        "schema_version":1,
        "kind":"vm_opcode_0x56_terminal_source_ownership_audit",
        "terminal_0x56_total":len(rows56),
        "counts":dict(sorted(counts.items())),
        "canonical_rom_verified":rom is not None,
        "byte_exact_terminal_56_operands_b0_verified":byte_audits,
        "rom_validation_issues":issues,
        "owner_trace_queue":ready,
        "normal_mode_requirement":"VM opcode 0x56 handler meaning is mode-dependent; the normal-mode C4:8B6A transition handler must be proven active for execution.",
        "source_assignment_policy":"The script pack, event record, source-selection pointer or even identical destination pack is not independent proof of active player map; no source ID promotion without runtime/ROM caller-state proof.",
        "source_selection_caveat":"The seven source-linked records carry A4-style data/source selection sites within event frames. These are NOT a reconstructed VM callgraph or proof of control-flow reaching the 0x56 opcode. Address order is diagnostic only, not runtime execution order.",
    }
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--rom",type=Path,default=None,help="Canonical local ROM, validated SHA256/size. Never committed.")
    parser.add_argument("--output",type=Path,default=OUT)
    args=parser.parse_args()
    rom=None
    if args.rom:
        rom=args.rom.read_bytes()
        if len(rom)!=EXPECTED_SIZE or hashlib.sha256(rom).hexdigest().upper()!=EXPECTED_SHA:
            raise SystemExit("ROM size/SHA-256 mismatch: refusing audit.")
    derived_path=ROOT/"viewer/data/world.json"
    derived=json.loads(derived_path.read_text(encoding="utf-8")).get("transition_candidates",[])
    report=audit(read_csv(CANDIDATES),read_csv(FRAMES),read_csv(XREF),rom,derived)
    if report["rom_validation_issues"]:
        raise SystemExit(f"Independent ROM/record audit failed: {report['rom_validation_issues'][:10]}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="owner_trace_queue"},ensure_ascii=False))


if __name__=="__main__":
    main()
