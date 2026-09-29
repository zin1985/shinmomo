#!/usr/bin/env python3
"""Catalog exact terminal VM opcode 0x54 saved-map-state return candidates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import catalog_map_selectors as cms

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

COLUMNS = [
    "source_config_id", "source_pack", "script_pack", "script_record",
    "script_entry", "trigger_type", "trigger_addr", "event_record",
    "event_sources", "destination_pack", "destination_config_id",
    "destination_x", "destination_y", "target_mode", "condition",
    "confidence", "evidence", "provenance",
]

def cpu_addr(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"

def cpu_to_file(text: str) -> int:
    bank, addr = text.split(":")
    return ((int(bank, 16) - 0xC0) << 16) | int(addr, 16)

def hx(v: int) -> str:
    return f"0x{v:02X}"

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def current_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out", type=Path,
        default=Path("data/maps/transitions/saved_state_return_candidates.csv"),
    )
    ap.add_argument(
        "--summary", type=Path,
        default=Path("data/maps/transitions/saved_state_return_summary.json"),
    )
    ap.add_argument(
        "--doc", type=Path,
        default=Path("docs/analysis/map_saved_state_return_catalog.md"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")

    frame_rows = read_csv(root / "data/events/event_record_frame_catalog.csv")
    source_rows = read_csv(root / "data/events/event_source_crosslink.csv")

    frames_by_family: dict[int, list[dict]] = defaultdict(list)
    for frame in frame_rows:
        item = dict(frame)
        item["_start"] = cpu_to_file(frame["record_start"])
        item["_end"] = cpu_to_file(frame["record_end_exclusive"])
        frames_by_family[int(frame["family_id"])].append(item)

    sources_by_record: dict[str, list[str]] = defaultdict(list)
    for xref in source_rows:
        label = f"{xref['subindex_hex']}->{xref['selected_source_cpu']}"
        if label not in sources_by_record[xref["record_id"]]:
            sources_by_record[xref["record_id"]].append(label)

    def event_context(pack_id: int, trigger_addr: str) -> tuple[str, str]:
        off = cpu_to_file(trigger_addr)
        for frame in frames_by_family.get(pack_id, []):
            if frame["_start"] <= off < frame["_end"]:
                rid = frame["record_id"]
                return rid, ";".join(sources_by_record.get(rid, []))
        return "", ""

    rows: list[dict] = []
    for script_pack in range(cms.FIRST_REAL_PACK, cms.LAST_REAL_PACK + 1):
        pack = cms.parse_pack(rom, script_pack)
        if not pack:
            continue
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 2 or body[-2:] != b"\x54\xB0":
                    continue
                addr = cpu_addr(entry["end"] - 2)
                record_id, event_sources = event_context(script_pack, addr)
                row = {c: "" for c in COLUMNS}
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x54_saved_state_return_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "event_sources": event_sources,
                    "target_mode": "indexed_saved_map_state",
                    "condition": (
                        "exact bounded VM-substream tail 54 B0; destination is "
                        "runtime-dependent saved state and is deliberately left blank"
                    ),
                    "confidence": "strong_candidate",
                    "evidence": (
                        "C4:8B4F opcode 0x54 calls 81:895A. 81:895A copies "
                        "$0305 to $15CF, sets transition bits in $DE, clears "
                        "$13B8 and $1984. Engine path C1:97BC checks $13B8 and "
                        "calls 81:8244 when zero; C1:8244 restores indexed saved "
                        "map state $151D..$1522, including pack via C1:8255."
                    ),
                    "provenance": (
                        f"canonical_rom_sha256={sha};"
                        "tools/python/catalog_saved_state_return_candidates.py;"
                        "C4:8B4F;C1:895A;C1:97BC;C1:97C1;C1:8244;C1:8255"
                    ),
                })
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    by_pack: dict[str, int] = defaultdict(int)
    for row in rows:
        by_pack[row["script_pack"]] += 1

    summary = {
        "schema_version": 1,
        "kind": "saved_state_return_candidate_catalog",
        "generated_against_git_head": current_head(root),
        "rom_sha256": sha,
        "candidate_count": len(rows),
        "confidence": "strong_candidate",
        "unique_script_pack_count": len(by_pack),
        "script_pack_counts": dict(sorted(by_pack.items())),
        "event_record_crosslink_count": sum(bool(r["event_record"]) for r in rows),
        "event_source_crosslink_count": sum(bool(r["event_sources"]) for r in rows),
        "handler_chain": {
            "opcode_0x54": "C4:8B4F",
            "transition_request_helper": "C1:895A",
            "restore_gate": "C1:97BC..97C5",
            "saved_state_restore": "C1:8244",
            "pack_restore_write": "C1:8255",
        },
        "runtime_anchor": {
            "evidence_file": "data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json",
            "edge": "0x50 -> 0x4C",
            "relation_status": "confirmed_runtime_transition",
            "static_opcode54_match": None,
            "note": (
                "The runtime edge behavior is compatible with saved-state restore, "
                "but the execution PC was not captured and no exact 0x54 row is "
                "promoted to confirmed."
            ),
        },
        "unresolved": [
            "source map/config cannot be inferred from script_pack",
            "destination pack/config/coordinates are dynamic saved-state values",
            "runtime execution PC is needed to bind a specific 0x54 row to the confirmed 0x50 -> 0x4C edge",
        ],
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc = f"""# Saved-state map return candidate catalog

Updated: 2026-09-29

This catalog covers VM opcode 0x54 separately from explicit-destination
opcodes 0x53/0x55/0x56.

## Handler chain

- 0x54 dispatches to C4:8B4F.
- C4:8B4F calls 81:895A.
- 81:895A saves current pack $0305 into $15CF, sets transition bits in $DE,
  clears $13B8, and clears $1984.
- C1:97BC tests $13B8. When zero, C1:97C1 calls 81:8244.
- C1:8244 restores indexed map state from $151D..$1522.
- C1:8255 is the restore write into $0305.

This is therefore a destination-indirect transition family: unlike 0x53,
0x55 and 0x56, the destination is not encoded beside the opcode.

## Conservative extraction

Only exact bounded substreams ending in 54 B0 are cataloged. Raw 0x54 bytes
inside arbitrary data or non-terminal streams are not promoted.

Candidates: **{len(rows)}**
Unique script packs: **{len(by_pack)}**
Event-record crosslinks: **{sum(bool(r['event_record']) for r in rows)}**
Event-source crosslinks: **{sum(bool(r['event_sources']) for r in rows)}**

Source map/config and destination fields stay blank unless independently
proven. In particular, script pack must not be treated as source map pack.

## Runtime anchor

The existing 2026-09-29 runtime evidence confirms 旅立ちの村 / pack 0x50
returning to world map pack 0x4C at coordinate (54,237). That behavior is
compatible with saved-map-state restore, but the execution PC was not captured.
No individual 0x54 candidate is therefore marked confirmed.

## Outputs

- data/maps/transitions/saved_state_return_candidates.csv
- data/maps/transitions/saved_state_return_summary.json
- docs/analysis/map_saved_state_return_catalog.md
- tools/python/catalog_saved_state_return_candidates.py
"""
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(doc, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
