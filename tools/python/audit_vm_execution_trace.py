#!/usr/bin/env python3
"""Fail-closed audit of an isolated, no-input BizHawk VM execution trace.

Observations are never promoted to a source map without independent active
map-config/VM-mode/entry evidence. Writes only local files next to trace.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/maps/transitions/map_transition_candidates.csv"
ROM_SHA = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
VM_HOOKS = {
    "vm56_map_transition", "vm25_async_schedule", "vm25_deferred_callback",
    "vm39_one_arg", "vm40_loop_six_args", "vm_pointer_advance_2"
}


def number(value):
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def cpu_from_file_offset(value):
    return f"{0xC0 + (value >> 16):02X}:{value & 0xFFFF:04X}"


def cpu_addr(value):
    if value is None or not 0xC00000 <= value <= 0xDFFFFF:
        return None
    return f"{value >> 16:02X}:{value & 0xFFFF:04X}"


def record_rom_offset(cpu_value):
    if cpu_value is None:
        return None
    if 0xC00000 <= cpu_value <= 0xDFFFFF:
        return cpu_value - 0xC00000
    return None


def inspect_trace(data, candidates, rom=None):
    if data.get("kind") != "isolated_vm_execution_trace":
        raise ValueError("Not an isolated VM execution trace")
    if data.get("input_sent") is not False:
        raise ValueError("Input must be explicitly recorded as not sent")
    requested = number(data.get("requested_neutral_frames"))
    advanced = number(data.get("advanced_frames"))
    if requested is None or not 1 <= requested <= 120 or advanced != requested:
        raise ValueError("Invalid requested/completed neutral frames")
    before = data.get("before", {})
    after = data.get("after", {})
    first, last = number(before.get("frame")), number(after.get("frame"))
    if first is None or last is None or last-first != advanced:
        raise ValueError("Snapshot frame span does not match frame advancement")
    if number(data.get("hook_registered")) is None or data["hook_registered"] < 1:
        raise ValueError("No execution hooks registered")
    if number(data.get("event_limit")) != 256:
        raise ValueError("Unexpected event limit")
    dropped = number(data.get("dropped_events"))
    if dropped is None or dropped < 0:
        raise ValueError("Missing or invalid dropped events")
    events = data.get("events")
    if not isinstance(events,list) or len(events)>256:
        raise ValueError("Trace events exceed bounded capture")
    indexed = {}
    for row in candidates:
        key = row.get("trigger_addr", "").upper()
        if key:
            indexed.setdefault(key, []).append(row)
    analyses = []
    counters = Counter()
    for event in events:
        frame = number(event.get("frame"))
        kind = event.get("hook")
        if frame is None or not first <= frame <= last or kind not in VM_HOOKS:
            raise ValueError(f"Unknown or out-of-frame execution event {event}")
        counters[kind] += 1
        ptr = number(event.get("vm_script_ptr_cpu"))
        yreg = number(event.get("cpu_y"))
        base = cpu_addr(ptr)
        effective = cpu_addr(ptr + yreg) if ptr is not None and yreg is not None and 0 <= yreg <= 65535 else None
        candidates_by_base = indexed.get(base or "", [])
        # Do not equate the operand fetch address with an opcode execution
        # address: it is displayed as a hypothesis only.
        exact_opcode = None
        if rom is not None and base:
            off = record_rom_offset(ptr)
            if off is not None and off<len(rom):
                exact_opcode = f"0x{rom[off]:02X}"
        analyses.append({
            "frame": frame,
            "hook": kind,
            "cpu_pc_observed": event.get("cpu_pc"),
            "cpu_pbr_observed": event.get("cpu_pbr"),
            "w0305_current_map_pack": event.get("w0305_map_pack"),
            "w035f_mode": event.get("w035f_vm_mode"),
            "w1398_dispatch": event.get("w1398_dispatch_mode"),
            "vm_script_pointer": base,
            "operand_fetch_cpu_estimate": effective,
            "rom_opcode_at_raw_pointer": exact_opcode,
            "catalog_candidates_at_exact_pointer": [
                {"trigger_addr":row.get("trigger_addr"), "script_pack":row.get("script_pack"),
                 "destination_pack":row.get("destination_pack"),
                 "destination_entry_id":row.get("destination_entry_id")}
                for row in candidates_by_base[:8]
            ],
            "handler_execution_observed": True,
            "source_map_configuration_proven": False,
            "current_story_predicate_proven": False,
            "notes": "Handler execution alone never identifies the active source map config; script pointer and Y are raw observations."
        })
    return {
        "schema_version": 1,
        "kind": "vm_execution_trace_audit",
        "start_frame": first, "end_frame": last,
        "neutral_frames_advanced": advanced,
        "hook_registration_count": data["hook_registered"],
        "hook_registration_errors": data.get("hook_errors") or "",
        "event_count": len(events),
        "dropped_events": dropped,
        "trace_complete_without_overflow": dropped == 0,
        "hook_counts": dict(sorted(counters.items())),
        "any_vm56_handler_executed": counters.get("vm56_map_transition",0)>0,
        "any_vm25_callback_executed": counters.get("vm25_deferred_callback",0)>0,
        "confirmed_source_map_bindings": 0,
        "classification": "Observed handler execution if present; never auto-promoted to playable graph edges.",
        "events": analyses
    }


def read_catalog(path):
    with path.open(encoding="utf-8-sig",newline="") as file:
        return list(csv.DictReader(file))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trace",type=Path,required=True,help="Local hidden-lab capture JSON")
    p.add_argument("--rom",type=Path,help="Optional canonical ROM for byte-level pointer checks")
    p.add_argument("--catalog",type=Path,default=CATALOG)
    p.add_argument("--output",type=Path,help="Defaults to trace sibling *_audit.json (not Git)")
    args=p.parse_args()
    rom=None
    if args.rom:
        rom=args.rom.read_bytes()
        if len(rom)!=2097152 or hashlib.sha256(rom).hexdigest().upper()!=ROM_SHA:
            raise SystemExit("Canonical ROM identity mismatch")
    report=inspect_trace(json.loads(args.trace.read_text(encoding="utf-8")),read_catalog(args.catalog),rom)
    out=args.output or args.trace.with_name(args.trace.stem+"_audit.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="events"},ensure_ascii=False))
    print("LOCAL_AUDIT_FILE="+str(out))


if __name__=="__main__":
    main()
