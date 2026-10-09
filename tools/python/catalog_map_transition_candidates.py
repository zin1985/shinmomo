#!/usr/bin/env python3
"""Catalog conservative Shinmomo map-transition candidates.

No ROM payload is written. Outputs contain only derived addresses, IDs,
configuration metadata, coordinates and evidence labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict, deque
from pathlib import Path

import catalog_map_selectors as cms

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

COLUMNS = [
    "source_config_id", "source_pack", "source_layout", "source_tileset",
    "script_pack", "script_record", "script_entry",
    "trigger_type", "trigger_addr", "event_record", "vm_context",
    "event_sources", "destination_pack", "destination_entry_id", "destination_config_id",
    "destination_layout", "destination_tileset", "destination_variant",
    "destination_x", "destination_y",
    "destination_secondary_x", "destination_secondary_y",
    "destination_coordinate_addr", "condition", "confidence",
    "evidence", "provenance",
]


def cpu_addr(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def cpu_to_file(text: str) -> int:
    bank_text, addr_text = text.split(":")
    return ((int(bank_text, 16) - 0xC0) << 16) | int(addr_text, 16)


def hx(value: int) -> str:
    return f"0x{value:02X}"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return ""


def coordinate_setter(rom: bytes, entry: dict | None) -> dict | None:
    """Recognize only instruction-aligned 0x58 forms proven by existing grammar."""
    if entry is None:
        return None
    body = rom[entry["start"]:entry["end"]]
    pos = None
    alignment = ""
    if len(body) >= 5 and body[0] == 0x58:
        pos, alignment = 0, "entry_start"
    elif len(body) >= 7 and body[0] == 0x96 and body[2] == 0x58:
        pos, alignment = 2, "proven_0x96_two_byte_prefix"
    if pos is None:
        return None
    return {
        "x": body[pos + 1],
        "y": body[pos + 2],
        "secondary_x": body[pos + 3],
        "secondary_y": body[pos + 4],
        "addr": cpu_addr(entry["start"] + pos),
        "alignment": alignment,
    }


def blank_row() -> dict:
    return {key: "" for key in COLUMNS}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/maps/transitions/map_transition_candidates.csv"),
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=Path("data/maps/transitions/map_transition_candidates_summary.json"),
    )
    ap.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analysis/map_transition_candidate_catalog.md"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")

    selector_rows = read_csv(root / "data/maps/selectors/primary_map_selector_catalog.csv")
    config_rows = read_csv(root / "data/maps/configurations/map_configuration_index.csv")
    frame_rows = read_csv(root / "data/events/event_record_frame_catalog.csv")
    source_xref_rows = read_csv(root / "data/events/event_source_crosslink.csv")
    config_by_id = {r["config_id"]: r for r in config_rows}
    config_by_tuple = {
        (int(r["primary_tileset_id"]), int(r["primary_layout_id"]), int(r["map_variant"])): r
        for r in config_rows
    }

    pack_configs: dict[int, set[str]] = defaultdict(set)
    for r in selector_rows:
        if (
            int(r["record_index"]) == 0
            and int(r["entry_id_dec"]) == 1
            and r["normal_mode_confirmed"].lower() == "true"
        ):
            key = (
                int(r["primary_tileset_id"]),
                int(r["primary_layout_id"]),
                int(r["map_variant"]),
            )
            cfg = config_by_tuple.get(key)
            if cfg:
                pack_configs[int(r["pack_id_dec"])].add(cfg["config_id"])

    frames_by_family: dict[int, list[dict]] = defaultdict(list)
    for frame in frame_rows:
        item = dict(frame)
        item["_start"] = cpu_to_file(frame["record_start"])
        item["_end"] = cpu_to_file(frame["record_end_exclusive"])
        frames_by_family[int(frame["family_id"])].append(item)

    sources_by_record: dict[str, list[str]] = defaultdict(list)
    for xref in source_xref_rows:
        label = f"{xref['subindex_hex']}->{xref['selected_source_cpu']}"
        if label not in sources_by_record[xref["record_id"]]:
            sources_by_record[xref["record_id"]].append(label)

    packs = {}
    for pack_id in range(cms.FIRST_REAL_PACK, cms.LAST_REAL_PACK + 1):
        parsed = cms.parse_pack(rom, pack_id)
        if parsed:
            packs[pack_id] = parsed


    def record0_entry(pack_id: int, entry_id: int) -> dict | None:
        pack = packs.get(pack_id)
        if not pack or not pack["records"]:
            return None
        header = cms.parse_record_header(rom, pack["records"][0])
        if not header:
            return None
        return next(
            (e for e in header["entries"] if e["entry_id"] == entry_id),
            None,
        )

    def pack_unique_entry(pack_id: int, entry_id: int) -> dict | None:
        """Return the unique matching entry anywhere in a parsed pack.

        Transition operand2 is treated conservatively: promotion is allowed
        only when exactly one parsed entry in the destination pack carries the
        requested entry ID. The returned copy records its owning record index
        for diagnostics/documentation.
        """
        pack = packs.get(pack_id)
        if not pack:
            return None
        matches = []
        for record in pack["records"]:
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                if entry["entry_id"] == entry_id:
                    item = dict(entry)
                    item["_record_index"] = record["record_index"]
                    matches.append(item)
        return matches[0] if len(matches) == 1 else None

    def destination_config(pack_id: int) -> dict | None:
        ids = pack_configs.get(pack_id, set())
        if len(ids) != 1:
            return None
        return config_by_id[next(iter(ids))]

    def event_context(pack_id: int, trigger_addr: str) -> tuple[str, str]:
        off = cpu_to_file(trigger_addr)
        for frame in frames_by_family.get(pack_id, []):
            if frame["_start"] <= off < frame["_end"]:
                record_id = frame["record_id"]
                return record_id, ";".join(sources_by_record.get(record_id, []))
        return "", ""

    def apply_destination(row: dict, pack_id: int, entry_id: int) -> tuple[bool, bool, int | None]:
        row["destination_pack"] = hx(pack_id)
        row["destination_entry_id"] = hx(entry_id)
        cfg = destination_config(pack_id)
        if cfg:
            row["destination_config_id"] = cfg["config_id"]
            row["destination_layout"] = cfg["primary_layout_id"]
            row["destination_tileset"] = cfg["primary_tileset_id"]
            row["destination_variant"] = cfg["map_variant"]
        entry = pack_unique_entry(pack_id, entry_id)
        coord = coordinate_setter(rom, entry)
        if coord:
            row["destination_x"] = coord["x"]
            row["destination_y"] = coord["y"]
            row["destination_secondary_x"] = coord["secondary_x"]
            row["destination_secondary_y"] = coord["secondary_y"]
            row["destination_coordinate_addr"] = coord["addr"]
        return (
            entry is not None,
            coord is not None,
            entry.get("_record_index") if entry is not None else None,
        )

    def route57_final(route_index: int) -> dict | None:
        if not 0 <= route_index < 16:
            return None
        table_off = cpu_to_file("C6:8060") + route_index * 2
        ptr = rom[table_off] | (rom[table_off + 1] << 8)
        pos = cpu_to_file(f"C6:{ptr:04X}")
        context_0306 = rom[pos]
        pos += 1
        nodes = []
        while pos + 3 < len(rom):
            pack_id = rom[pos]
            pos += 1
            if pack_id == 0:
                break
            x = rom[pos]
            y = rom[pos + 1]
            entrance = rom[pos + 2]
            pos += 3
            nodes.append((pack_id, x, y, entrance))
        if not nodes:
            return None
        pack_id, x, y, entrance = nodes[-1]
        return {
            "route_ptr": f"C6:{ptr:04X}",
            "context_0306": context_0306,
            "pack_id": pack_id,
            "x": x,
            "y": y,
            "entrance": entrance,
            "saved_node_count": max(0, len(nodes) - 1),
        }

    # Fail-closed control-flow decoder used to prove non-terminal 0x57
    # instruction boundaries and to classify every remaining raw 57 <00..0F>
    # shape. Unknown forms stop that path. A0 nested calls continue only when
    # their callee is independently proven to return; B1 is treated as a tail
    # jump rather than a fallthrough.
    cfg_safe_lengths = {
        0x01: 2, 0x04: 2, 0x06: 1, 0x08: 4, 0x09: 4,
        0x10: 2, 0x11: 2, 0x13: 2, 0x15: 3, 0x16: 3,
        0x17: 3, 0x18: 4, 0x19: 4, 0x1B: 4, 0x1C: 3,
        0x1E: 3, 0x1F: 3, 0x20: 3, 0x21: 3, 0x23: 1,
        0x28: 2, 0x2A: 1, 0x2D: 2, 0x2F: 7, 0x30: 6,
        0x31: 2, 0x33: 4, 0x41: 3, 0x43: 2, 0x47: 5,
        0x49: 6, 0x50: 4, 0x51: 3, 0x53: 3, 0x54: 1,
        0x55: 3, 0x56: 3, 0x57: 2, 0x58: 5, 0x59: 6,
        0x5D: 5, 0x5E: 2, 0x61: 1, 0x63: 5, 0x64: 2,
        0x67: 7, 0x69: 3, 0x70: 1, 0x71: 3, 0x74: 3,
        0x96: 2, 0xA1: 2, 0xA2: 2, 0xA3: 2, 0xA4: 2,
        0xE0: 1, 0xE1: 1, 0xE7: 1, 0xE8: 1, 0xEC: 1,
        0xED: 1, 0xF1: 1,
    }
    for _op in range(0xC0, 0xCE):
        cfg_safe_lengths[_op] = 1
    for _op in range(0xD0, 0xE0):
        cfg_safe_lengths[_op] = 3
    cfg_safe_lengths.update({
        0x0A: 4, 0x14: 2, 0x1A: 4, 0x42: 2, 0x4A: 5, 0x4F: 5,
        # 0x6E: normal VM dispatch table C4:87D4[0x6E] -> C4:93A9;
        # both handler branch arms jump to C4:895E (advance 2 bytes).
        # Independent canonical ROM verifier: verify_vm_opcode6e_handler.py.
        0x66: 4, 0x6C: 2, 0x6E: 2, 0x6F: 2, 0x80: 1, 0x89: 1,
        0xB6: 1, 0xEF: 1, 0xF0: 1,
    })

    cfg_entries = []
    for _sp, _pack in sorted(packs.items()):
        for _record in _pack["records"]:
            if (_sp, _record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            _header = cms.parse_record_header(rom, _record)
            if not _header:
                continue
            for _entry in _header["entries"]:
                cfg_entries.append(
                    (
                        _entry["start"], _entry["end"], _sp,
                        _record["record_index"], _entry["entry_id"],
                    )
                )

    def signed8(value: int) -> int:
        return value - 0x100 if value & 0x80 else value

    def cfg_ptr_file(ptr: int) -> int:
        bank = (ptr >> 16) & 0xFF
        return ((bank - 0xC0) << 16) | (ptr & 0xFFFF)

    def cfg_bound_for(off: int):
        exact = [item for item in cfg_entries if item[0] == off]
        if exact:
            return exact[0]
        inside = [item for item in cfg_entries if item[0] <= off < item[1]]
        return inside[0] if len(inside) == 1 else None

    def cfg_opcode_length(body: bytes, pos: int) -> int | None:
        op = body[pos]

        # Opcode 0x02 dispatches through 84:9BEE. These concrete operands have
        # independently inspected RTL-returning targets, while C4:895E advances
        # the caller by two bytes before the indirect call.
        # Operand 0x13 -> table C4:9C24 -> 83:BBAB, with a concrete RTL
        # after JSL 80:AC14 (see verify_vm_opcode02_13_handler.py).
        if op == 0x02:
            if pos + 2 <= len(body) and body[pos + 1] in {0x13, 0x17, 0x1D, 0x25, 0x2D, 0x41, 0x5C, 0x5E}:
                return 2
            return None

        # Sign bit of the first 16-bit operand selects a 3- or 4-byte form.
        if op == 0x22:
            if pos + 3 > len(body):
                return None
            word = body[pos + 1] | (body[pos + 2] << 8)
            return 4 if word & 0x8000 else 3

        # Only the inspected 0x3D subtypes needed by the route CFG are admitted.
        if op == 0x3D:
            if pos + 2 > len(body):
                return None
            subtype = body[pos + 1]
            if subtype == 0x02:
                return 3
            if subtype in {0x03, 0x04, 0x05, 0x06}:
                return 2
            if subtype == 0x29:
                return 5
            return None

        if op == 0x45:
            if pos + 2 > len(body):
                return None
            return 2 if body[pos + 1] == 0 else 5

        if op == 0x52:
            if pos + 2 > len(body):
                return None
            return 6 if body[pos + 1] >= 0xFE else 5

        if op == 0x5B:
            if pos + 3 > len(body):
                return None
            subtype = body[pos + 2]
            if subtype == 1:
                return 4
            if subtype == 2:
                return 5
            if subtype in {3, 4}:
                return 3
            return 5

        # Zero-terminated pair list; FF terminates after its 16-bit extension.
        if op == 0x68:
            q = pos + 1
            while q < len(body):
                value = body[q]
                q += 1
                if value == 0:
                    return q - pos
                if value == 0xFF:
                    if q + 2 > len(body):
                        return None
                    q += 2
                    return q - pos
                if q >= len(body):
                    return None
                q += 1
            return None

        if op == 0x72:
            if pos + 3 > len(body):
                return None
            return 11 if body[pos + 1] == 0xFF and body[pos + 2] == 0xFF else 3

        # Concrete 0x7B subtype used by the residual route corpus.
        if op == 0x7B:
            if pos + 2 <= len(body) and body[pos + 1] == 0x01:
                return 3
            return None

        if op == 0xCE:
            return 2 if pos + 2 <= len(body) else None
        if op == 0xCF:
            return 3 if pos + 3 <= len(body) else None

        return cfg_safe_lengths.get(op)

    cfg_return_memo: dict[int, tuple[bool, bool, set[str]]] = {}
    cfg_return_visiting: set[int] = set()

    def cfg_prove_return(ptr: int, depth: int = 0) -> tuple[bool, bool, set[str]]:
        if ptr in cfg_return_memo:
            return cfg_return_memo[ptr]
        if ptr in cfg_return_visiting or depth > 16:
            return False, False, {"cycle_or_depth"}

        start = cfg_ptr_file(ptr)
        bound = cfg_bound_for(start)
        if not bound:
            return False, False, {"no_entry_bound"}

        entry_start, entry_end, _, _, _ = bound
        body = rom[entry_start:entry_end]
        start_pos = start - entry_start
        cfg_return_visiting.add(ptr)
        queue = deque([start_pos])
        seen: set[int] = set()
        found_return = False
        blockers: set[str] = set()

        while queue:
            pos = queue.popleft()
            if pos in seen:
                continue
            seen.add(pos)
            if not (start_pos <= pos < len(body)):
                blockers.add("escape")
                continue

            op = body[pos]
            if op in {0xB0, 0xB5}:
                found_return = True
                continue
            if op in {0x7D, 0x8C}:
                # Both table entries dispatch to C4:8963, whose first
                # instruction is BRK. These are proven non-returning VM trap
                # paths, not unknown instruction boundaries.
                continue

            if op in {0xB2, 0xB3, 0xB4}:
                if pos + 2 > len(body):
                    blockers.add("truncated_branch")
                    continue
                target = pos + signed8(body[pos + 1])
                if op in {0xB3, 0xB4}:
                    queue.append(pos + 2)
                queue.append(target)
                continue

            if op == 0xB1:
                if pos + 4 > len(body):
                    blockers.add("truncated_B1")
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                child_off = cfg_ptr_file(child)
                if entry_start <= child_off < entry_end:
                    queue.append(child_off - entry_start)
                else:
                    ok, returned, child_blockers = cfg_prove_return(child, depth + 1)
                    if ok and returned:
                        found_return = True
                    elif not returned and not child_blockers:
                        # Proven tail path that never returns.
                        pass
                    else:
                        blockers.add(f"B1:{child >> 16:02X}:{child & 0xFFFF:04X}")
                        blockers.update(child_blockers)
                continue

            if op == 0xA0:
                if pos + 4 > len(body):
                    blockers.add("truncated_A0")
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                ok, returned, child_blockers = cfg_prove_return(child, depth + 1)
                if ok and returned:
                    queue.append(pos + 4)
                elif not returned and not child_blockers:
                    # Proven non-returning nested call terminates this path.
                    pass
                else:
                    blockers.add(f"A0:{child >> 16:02X}:{child & 0xFFFF:04X}")
                    blockers.update(child_blockers)
                continue

            length = cfg_opcode_length(body, pos)
            if length is None:
                blockers.add(f"op:{op:02X}")
                continue
            if pos + length > len(body):
                blockers.add("truncated")
                continue
            queue.append(pos + length)

        cfg_return_visiting.remove(ptr)
        result = (found_return and not blockers, found_return, blockers)
        cfg_return_memo[ptr] = result
        return result

    def cfg_reachable_57_offsets(body: bytes, entry_start: int) -> list[int]:
        queue = deque([0])
        seen: set[int] = set()
        found: set[int] = set()
        while queue:
            pos = queue.popleft()
            if pos in seen or not (0 <= pos < len(body)):
                continue
            seen.add(pos)
            op = body[pos]

            if op in {0xB0, 0xB5}:
                continue
            if op in {0x7D, 0x8C}:
                continue

            if op in {0xB2, 0xB3, 0xB4}:
                if pos + 2 > len(body):
                    continue
                target = pos + signed8(body[pos + 1])
                if op in {0xB3, 0xB4}:
                    queue.append(pos + 2)
                queue.append(target)
                continue

            if op == 0xB1:
                if pos + 4 > len(body):
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                child_off = cfg_ptr_file(child)
                if entry_start <= child_off < entry_start + len(body):
                    queue.append(child_off - entry_start)
                continue

            if op == 0xA0:
                if pos + 4 > len(body):
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                ok, returned, _ = cfg_prove_return(child)
                if ok and returned:
                    queue.append(pos + 4)
                continue

            length = cfg_opcode_length(body, pos)
            if length is None or pos + length > len(body):
                continue
            if op == 0x57 and pos + 1 < len(body) and body[pos + 1] < 16:
                found.add(pos)
            queue.append(pos + length)
        return sorted(found)

    def cfg_target_reachability(
        body: bytes, entry_start: int, target_pos: int
    ) -> tuple[bool, set[str]]:
        queue = deque([0])
        seen: set[int] = set()
        blockers: set[str] = set()

        while queue:
            pos = queue.popleft()
            if pos in seen or not (0 <= pos < len(body)):
                continue
            seen.add(pos)
            if pos == target_pos:
                return True, set()

            op = body[pos]
            if op in {0xB0, 0xB5}:
                continue
            if op in {0x7D, 0x8C}:
                continue

            if op in {0xB2, 0xB3, 0xB4}:
                if pos + 2 > len(body):
                    blockers.add("truncated_branch")
                    continue
                target = pos + signed8(body[pos + 1])
                if op in {0xB3, 0xB4}:
                    queue.append(pos + 2)
                queue.append(target)
                continue

            if op == 0xB1:
                if pos + 4 > len(body):
                    blockers.add("truncated_B1")
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                child_off = cfg_ptr_file(child)
                if entry_start <= child_off < entry_start + len(body):
                    queue.append(child_off - entry_start)
                continue

            if op == 0xA0:
                if pos + 4 > len(body):
                    blockers.add("truncated_A0")
                    continue
                child = body[pos + 1] | (body[pos + 2] << 8) | (body[pos + 3] << 16)
                ok, returned, child_blockers = cfg_prove_return(child)
                if ok and returned:
                    queue.append(pos + 4)
                elif not returned and not child_blockers:
                    # Proven non-returning nested call terminates this path.
                    pass
                else:
                    blockers.add(f"A0:{child >> 16:02X}:{child & 0xFFFF:04X}")
                    blockers.update(child_blockers)
                continue

            length = cfg_opcode_length(body, pos)
            if length is None:
                blockers.add(f"op:{op:02X}")
                continue
            if pos + length > len(body):
                blockers.add("truncated")
                continue
            queue.append(pos + length)

        return False, blockers

    rows: list[dict] = []
    seen_triggers: set[str] = set()

    # Runtime-confirmed edge already preserved in canonical evidence.
    confirmed = blank_row()
    confirmed.update({
        "source_config_id": "cfg_t07_l015_v2",
        "source_pack": "0x2E",
        "source_layout": "15",
        "source_tileset": "7",
        "trigger_type": "runtime_observed_map_transition",
        "destination_pack": "0x50",
        "destination_entry_id": "",
        "destination_config_id": "cfg_t04_l008_v2",
        "destination_layout": "8",
        "destination_tileset": "4",
        "destination_variant": "2",
        "condition": (
            "walk south through the central-room exit; exact event opcode "
            "address is not yet identified"
        ),
        "confidence": "confirmed",
        "evidence": (
            "runtime trace shows $0305 0x2E->0x50, then $126E/$12B4 converge "
            "to 0x50 and selector 4/8/2 becomes active"
        ),
        "provenance": (
            "data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json;"
            "docs/analysis/map_runtime_transition_pack2e_to_pack50_20260928.md"
        ),
    })
    rows.append(confirmed)

    terminal_count = 0
    terminal_dest_entry = 0
    terminal_nonrecord0_entry = 0
    terminal_coord = 0
    nonterminal_coord = 0
    terminal53_count = 0
    terminal53_dest_entry = 0
    terminal53_nonrecord0_entry = 0
    terminal53_coord = 0
    nonterminal53_coord = 0
    terminal55_count = 0
    terminal55_dest_entry = 0
    terminal55_nonrecord0_entry = 0
    terminal55_coord = 0
    nonterminal55_coord = 0
    nonterminal56_cfg_promoted = 0
    nonterminal56_cfg_dropped_unreachable = 0
    nonterminal56_cfg_blocked = 0
    nonterminal53_cfg_promoted = 0
    nonterminal53_cfg_dropped_unreachable = 0
    nonterminal53_cfg_blocked = 0
    nonterminal55_cfg_promoted = 0
    nonterminal55_cfg_dropped_unreachable = 0
    nonterminal55_cfg_blocked = 0
    terminal57_count = 0
    entry_start57_count = 0
    cfg_reachable57_count = 0
    terminal_unresolved_cfg_promoted = Counter()
    terminal_unresolved_cfg_dropped = Counter()
    terminal_unresolved_cfg_blocked = Counter()
    terminal_unresolved_cfg_promoted_addrs: list[str] = []
    terminal_unresolved_cfg_dropped_addrs: list[str] = []
    terminal_unresolved_cfg_blocked_addrs: list[str] = []

    def audit_unresolved_terminal(
        body: bytes, entry: dict, addr: str, opcode: int
    ) -> tuple[str, set[str]]:
        reachable, blockers = cfg_target_reachability(
            body, entry["start"], len(body) - 4
        )
        key = f"0x{opcode:02X}"
        if reachable:
            terminal_unresolved_cfg_promoted[key] += 1
            terminal_unresolved_cfg_promoted_addrs.append(addr)
            return "promoted", blockers
        if blockers:
            terminal_unresolved_cfg_blocked[key] += 1
            terminal_unresolved_cfg_blocked_addrs.append(addr)
            return "blocked", blockers
        terminal_unresolved_cfg_dropped[key] += 1
        terminal_unresolved_cfg_dropped_addrs.append(addr)
        return "dropped", blockers

    # Conservative static family: bounded substreams whose exact tail is
    # 56 <destination_pack> <destination_entry> B0.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue

            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x56 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal_count += 1

                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x56_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists, dest_record_index = apply_destination(
                    row, dest_pack, dest_entry
                )
                if dest_exists:
                    terminal_dest_entry += 1
                    if dest_record_index not in (None, 0):
                        terminal_nonrecord0_entry += 1
                    row["confidence"] = "strong_candidate"
                    if dest_record_index == 0:
                        row["condition"] = (
                            f"bounded substream tail; destination record0 entry "
                            f"{hx(dest_entry)} exists"
                        )
                    else:
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} exists in record {dest_record_index}"
                        )
                else:
                    terminal_cfg_status, terminal_cfg_blockers = audit_unresolved_terminal(
                        body, entry, addr, 0x56
                    )
                    if terminal_cfg_status == "dropped":
                        terminal_count -= 1
                        continue
                    if terminal_cfg_status == "promoted":
                        row["confidence"] = "strong_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source opcode boundary "
                            "is CFG-reachable"
                        )
                    else:
                        row["confidence"] = "structural_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source CFG blockers: "
                            + "|".join(sorted(terminal_cfg_blockers))
                        )
                if coord_exists:
                    terminal_coord += 1

                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B6A handler for opcode 0x56 stores operand1 to $15D0/$0305, "
                    "copies old $0305 to $15CF, stores operand2 to $13B8/$13B9, "
                    "calls 81:837F, and advances three bytes; exact bounded tail "
                    "ends in compact B0"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination entry operands "
                        "to $1573/$157D/$15C3/$15C4"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "tools/python/catalog_map_selectors.py;"
                    "C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)

    # Preserve non-terminal shapes only when the destination entry itself has
    # an aligned 0x58 coordinate setter. Opcode boundary at the source remains
    # intentionally unpromoted, so these stay structural candidates.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x56:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue

                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue

                    reachable, reachability_blockers = cfg_target_reachability(
                        body, entry["start"], pos
                    )
                    if not reachable and not reachability_blockers:
                        nonterminal56_cfg_dropped_unreachable += 1
                        continue
                    if reachable:
                        nonterminal56_cfg_promoted += 1
                    else:
                        nonterminal56_cfg_blocked += 1

                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x56_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": (
                            "strong_candidate" if reachable else "structural_candidate"
                        ),
                        "condition": (
                            (
                                "source opcode boundary proven reachable by fail-closed CFG; "
                                "destination record0 entry exists and has aligned 0x58 setter"
                            )
                            if reachable else
                            (
                                "source opcode boundary not yet proven; destination "
                                "record0 entry exists and has aligned 0x58 setter; "
                                "CFG blockers=" + ",".join(sorted(reachability_blockers))
                            )
                        ),
                        "evidence": (
                            "raw 0x56 shape inside a structurally bounded VM substream; "
                            "destination pack/entry cross-links to aligned opcode 0x58 "
                            "coordinate setter; "
                            + (
                                "source opcode boundary proven reachable by fail-closed CFG"
                                if reachable else
                                "source opcode boundary remains blocked by fail-closed CFG"
                            )
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal_coord += 1


    # Opcode 0x53 is a transition wrapper: C4:8B3F performs pre-work and
    # directly JSRs C4:8B6A, so it inherits the same two transition operands.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x53 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal53_count += 1
                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x53_transition_wrapper_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists, dest_record_index = apply_destination(row, dest_pack, dest_entry)
                if dest_exists:
                    terminal53_dest_entry += 1
                    if dest_record_index not in (None, 0):
                        terminal53_nonrecord0_entry += 1
                    row["confidence"] = "strong_candidate"
                    if dest_record_index == 0:
                        row["condition"] = (
                            f"bounded substream tail; destination record0 entry "
                            f"{hx(dest_entry)} exists"
                        )
                    else:
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} exists in record {dest_record_index}"
                        )
                else:
                    terminal_cfg_status, terminal_cfg_blockers = audit_unresolved_terminal(
                        body, entry, addr, 0x53
                    )
                    if terminal_cfg_status == "dropped":
                        terminal53_count -= 1
                        continue
                    if terminal_cfg_status == "promoted":
                        row["confidence"] = "strong_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source opcode boundary "
                            "is CFG-reachable"
                        )
                    else:
                        row["confidence"] = "structural_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source CFG blockers: "
                            + "|".join(sorted(terminal_cfg_blockers))
                        )
                if coord_exists:
                    terminal53_coord += 1
                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B3F opcode 0x53 wrapper calls C4:8B6A transition core; "
                    "the core writes operand1 to $0305 and operand2 to $13B8/$13B9; "
                    "exact bounded tail ends in compact B0"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination coordinates"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "C4:8B3F;C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)


    # Non-terminal 0x53 shapes stay structural unless destination coordinates
    # independently anchor the same destination pack/entry relation.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x53:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue
                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue

                    reachable, reachability_blockers = cfg_target_reachability(
                        body, entry["start"], pos
                    )
                    if not reachable and not reachability_blockers:
                        nonterminal53_cfg_dropped_unreachable += 1
                        continue
                    if reachable:
                        nonterminal53_cfg_promoted += 1
                    else:
                        nonterminal53_cfg_blocked += 1

                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x53_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": (
                            "strong_candidate" if reachable else "structural_candidate"
                        ),
                        "condition": (
                            (
                                "source opcode boundary proven reachable by fail-closed CFG; "
                                "destination record0 entry exists and has aligned 0x58 setter"
                            )
                            if reachable else
                            (
                                "source opcode boundary not yet proven; destination "
                                "record0 entry exists and has aligned 0x58 setter; "
                                "CFG blockers=" + ",".join(sorted(reachability_blockers))
                            )
                        ),
                        "evidence": (
                            "raw 0x53 shape inside bounded VM substream; C4:8B3F "
                            "is the transition wrapper for C4:8B6A; destination "
                            "entry independently has aligned 0x58 coordinates; "
                            + (
                                "source opcode boundary proven reachable by fail-closed CFG"
                                if reachable else
                                "source opcode boundary remains blocked by fail-closed CFG"
                            )
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B3F;C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal53_coord += 1


    # Opcode 0x55 restores an indexed saved map state through 81:8244,
    # preserves the current primary X/Y pair, then falls through to the
    # C4:8B6A transition core. It therefore uses the same explicit
    # <destination_pack> <destination_entry> operand pair as 0x56.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x55 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal55_count += 1
                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x55_restore_context_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists, dest_record_index = apply_destination(
                    row, dest_pack, dest_entry
                )
                if dest_exists:
                    terminal55_dest_entry += 1
                    if dest_record_index not in (None, 0):
                        terminal55_nonrecord0_entry += 1
                    row["confidence"] = "strong_candidate"
                    if dest_record_index == 0:
                        row["condition"] = (
                            f"bounded substream tail; destination record0 entry "
                            f"{hx(dest_entry)} exists"
                        )
                    else:
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} exists in record {dest_record_index}"
                        )
                else:
                    terminal_cfg_status, terminal_cfg_blockers = audit_unresolved_terminal(
                        body, entry, addr, 0x55
                    )
                    if terminal_cfg_status == "dropped":
                        terminal55_count -= 1
                        continue
                    if terminal_cfg_status == "promoted":
                        row["confidence"] = "strong_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source opcode boundary "
                            "is CFG-reachable"
                        )
                    else:
                        row["confidence"] = "structural_candidate"
                        row["condition"] = (
                            f"bounded substream tail; destination pack-wide unique entry "
                            f"{hx(dest_entry)} not resolved; source CFG blockers: "
                            + "|".join(sorted(terminal_cfg_blockers))
                        )
                if coord_exists:
                    terminal55_coord += 1
                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B56 opcode 0x55 saves current $157D/$1573 on the CPU "
                    "stack, calls 81:8244 to restore indexed map state, restores "
                    "the current primary X/Y pair, then falls through to C4:8B6A; "
                    "the transition core writes operand1 to $0305 and operand2 "
                    "to $13B8/$13B9"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination coordinates"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "C4:8B56;C1:8244;C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)

    # Non-terminal 0x55 shapes are kept only when destination coordinates
    # independently anchor the destination pack/entry relationship.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x55:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue
                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue

                    reachable, reachability_blockers = cfg_target_reachability(
                        body, entry["start"], pos
                    )
                    if not reachable and not reachability_blockers:
                        nonterminal55_cfg_dropped_unreachable += 1
                        continue
                    if reachable:
                        nonterminal55_cfg_promoted += 1
                    else:
                        nonterminal55_cfg_blocked += 1

                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x55_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": (
                            "strong_candidate" if reachable else "structural_candidate"
                        ),
                        "condition": (
                            (
                                "source opcode boundary proven reachable by fail-closed CFG; "
                                "destination record0 entry exists and has aligned 0x58 setter"
                            )
                            if reachable else
                            (
                                "source opcode boundary not yet proven; destination "
                                "record0 entry exists and has aligned 0x58 setter; "
                                "CFG blockers=" + ",".join(sorted(reachability_blockers))
                            )
                        ),
                        "evidence": (
                            "raw 0x55 shape inside bounded VM substream; C4:8B56 "
                            "restores saved map context then falls through to the "
                            "C4:8B6A transition core; destination entry independently "
                            "has aligned 0x58 coordinates; "
                            + (
                                "source opcode boundary proven reachable by fail-closed CFG"
                                if reachable else
                                "source opcode boundary remains blocked by fail-closed CFG"
                            )
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B56;C1:8244;C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal55_coord += 1


    # Opcode 0x57 selects one of the 16 native C6:8000 route-stack
    # definitions. Only exact terminal 57 <index> B0 forms are promoted here;
    # non-terminal raw 0x57 shapes remain unpromoted until source opcode
    # alignment is proven.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 3 or body[-3] != 0x57 or body[-1] != 0xB0:
                    continue
                route_index = body[-2]
                route = route57_final(route_index)
                if route is None:
                    continue
                addr = cpu_addr(entry["end"] - 3)
                seen_triggers.add(addr)
                terminal57_count += 1
                record_id, event_sources = event_context(script_pack, addr)

                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x57_native_route_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                    "destination_pack": hx(route["pack_id"]),
                    "destination_x": route["x"],
                    "destination_y": route["y"],
                    "confidence": "strong_candidate",
                    "condition": (
                        f"exact bounded tail 57 {hx(route_index)} B0; "
                        f"C4:8BD4 guard $13B8 != 0; route_ptr={route['route_ptr']}; "
                        f"context_0306={hx(route['context_0306'])}; "
                        f"destination_entrance={hx(route['entrance'])}"
                    ),
                    "evidence": (
                        "C4:8BD4 opcode 0x57 reads one route-index operand when "
                        "$13B8 != 0 and JSLs 86:8000 (LoROM mirror of C6:8000). "
                        "C6:8000 doubles the index, loads a route pointer from "
                        "C6:8060, clears the saved-map-state stack via 81:8204, "
                        "walks [pack,x,y,entrance] nodes, saves non-final nodes "
                        "through 81:8207, and leaves the final node active"
                    ),
                    "provenance": (
                        f"canonical_rom_sha256={sha};"
                        "tools/python/catalog_map_transition_candidates.py;"
                        "C4:8BD4;C6:8000;C6:8060;81:8204;81:8207"
                    ),
                })
                cfg = destination_config(route["pack_id"])
                if cfg:
                    row["destination_config_id"] = cfg["config_id"]
                    row["destination_layout"] = cfg["primary_layout_id"]
                    row["destination_tileset"] = cfg["primary_tileset_id"]
                    row["destination_variant"] = cfg["map_variant"]
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)


    # A second high-confidence 0x57 family begins at an independently
    # proven entry boundary. These rows are non-terminal but instruction
    # alignment is exact because byte 0 of the bounded entry is opcode 0x57.
    # When opcode 0x58 immediately follows, its aligned coordinate operands
    # replace the route-table final X/Y as the effective post-route position.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 2 or body[0] != 0x57:
                    continue
                route_index = body[1]
                route = route57_final(route_index)
                if route is None:
                    continue
                # Exact terminal forms are already cataloged above.
                if len(body) == 3 and body[2] == 0xB0:
                    continue

                addr = cpu_addr(entry["start"])
                if addr in seen_triggers:
                    continue
                seen_triggers.add(addr)
                entry_start57_count += 1
                record_id, event_sources = event_context(script_pack, addr)

                effective_x = route["x"]
                effective_y = route["y"]
                secondary_x = ""
                secondary_y = ""
                coordinate_addr = ""
                coord_note = "route-table final X/Y retained"
                if len(body) >= 7 and body[2] == 0x58:
                    effective_x = body[3]
                    effective_y = body[4]
                    secondary_x = body[5]
                    secondary_y = body[6]
                    coordinate_addr = cpu_addr(entry["start"] + 2)
                    coord_note = (
                        f"aligned immediate 0x58 at {coordinate_addr} overrides "
                        "primary/secondary coordinates"
                    )

                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x57_entry_start_route",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                    "destination_pack": hx(route["pack_id"]),
                    "destination_x": effective_x,
                    "destination_y": effective_y,
                    "destination_secondary_x": secondary_x,
                    "destination_secondary_y": secondary_y,
                    "destination_coordinate_addr": coordinate_addr,
                    "confidence": "strong_candidate",
                    "condition": (
                        f"entry-start instruction boundary; route_index={hx(route_index)}; "
                        f"route_ptr={route['route_ptr']}; "
                        f"context_0306={hx(route['context_0306'])}; "
                        f"destination_entrance={hx(route['entrance'])}; {coord_note}"
                    ),
                    "evidence": (
                        "entry byte 0 is opcode 0x57, so source opcode alignment is "
                        "independently exact. C4:8BD4 passes its one-byte route index "
                        "to 86:8000/C6:8000, which selects C6:8060 and constructs "
                        "the saved map-state route. "
                        + (
                            "The next aligned instruction is opcode 0x58, whose four "
                            "operands write $1573/$157D/$15C3/$15C4."
                            if coordinate_addr else
                            "No immediate aligned 0x58 follows, so the route-table "
                            "final coordinates are retained."
                        )
                    ),
                    "provenance": (
                        f"canonical_rom_sha256={sha};"
                        "tools/python/catalog_map_transition_candidates.py;"
                        "C4:8BD4;C6:8000;C6:8060;81:8204;81:8207"
                        + (";C4:8BE2" if coordinate_addr else "")
                    ),
                })
                cfg = destination_config(route["pack_id"])
                if cfg:
                    row["destination_config_id"] = cfg["config_id"]
                    row["destination_layout"] = cfg["primary_layout_id"]
                    row["destination_tileset"] = cfg["primary_tileset_id"]
                    row["destination_variant"] = cfg["map_variant"]
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)


    # Branch-reachable non-terminal 0x57 instructions. This pass uses a
    # fail-closed CFG from the parsed entry start: unknown/variable opcodes stop
    # a path, B2 is unconditional rel8, and B3/B4 explore both branch and
    # fallthrough. Rows already proven by terminal or entry-start rules are
    # skipped through seen_triggers.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in cfg_reachable_57_offsets(body, entry["start"]):
                    if pos == 0:
                        continue
                    # Exact terminal form was already cataloged above.
                    if pos == len(body) - 3 and body[-1] == 0xB0:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue
                    route_index = body[pos + 1]
                    route = route57_final(route_index)
                    if route is None:
                        continue

                    seen_triggers.add(addr)
                    cfg_reachable57_count += 1
                    record_id, event_sources = event_context(script_pack, addr)

                    effective_x = route["x"]
                    effective_y = route["y"]
                    secondary_x = ""
                    secondary_y = ""
                    coordinate_addr = ""
                    next_opcode = (
                        f"0x{body[pos + 2]:02X}"
                        if pos + 2 < len(body)
                        else ""
                    )
                    if pos + 7 <= len(body) and body[pos + 2] == 0x58:
                        effective_x = body[pos + 3]
                        effective_y = body[pos + 4]
                        secondary_x = body[pos + 5]
                        secondary_y = body[pos + 6]
                        coordinate_addr = cpu_addr(entry["start"] + pos + 2)

                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x57_cfg_reachable_route",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "destination_pack": hx(route["pack_id"]),
                        "destination_x": effective_x,
                        "destination_y": effective_y,
                        "destination_secondary_x": secondary_x,
                        "destination_secondary_y": secondary_y,
                        "destination_coordinate_addr": coordinate_addr,
                        "confidence": "strong_candidate",
                        "condition": (
                            "instruction boundary is reachable from parsed entry start "
                            "under fail-closed CFG; "
                            f"route_index={hx(route_index)}; route_ptr={route['route_ptr']}; "
                            f"context_0306={hx(route['context_0306'])}; "
                            f"destination_entrance={hx(route['entrance'])}; "
                            f"next_opcode={next_opcode}; "
                            + (
                                f"aligned immediate 0x58 at {coordinate_addr} "
                                "overrides primary/secondary coordinates"
                                if coordinate_addr else
                                "route-table final coordinates retained"
                            )
                        ),
                        "evidence": (
                            "C4:8BD4 opcode 0x57 route-index semantics are proven. "
                            "Source alignment is independently established by a "
                            "fail-closed control-flow walk from the parsed entry start "
                            "using only independently bounded instruction lengths and "
                            "the proven B2/B3/B4 relative-branch grammar. Unknown or "
                            "variable-length opcodes terminate that CFG path. "
                            + (
                                "The next aligned opcode is 0x58, whose four operands "
                                "write $1573/$157D/$15C3/$15C4."
                                if coordinate_addr else
                                ""
                            )
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "cfg_reachable_57_offsets;"
                            "C4:8BD4;C6:8000;C6:8060;81:8204;81:8207"
                            + (";C4:8BE2" if coordinate_addr else "")
                        ),
                    })
                    cfg = destination_config(route["pack_id"])
                    if cfg:
                        row["destination_config_id"] = cfg["config_id"]
                        row["destination_layout"] = cfg["primary_layout_id"]
                        row["destination_tileset"] = cfg["primary_tileset_id"]
                        row["destination_variant"] = cfg["map_variant"]
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    rows.append(row)


    # Promote static transition rows only when a canonical runtime evidence file
    # names the exact static trigger and all destination fields agree.
    runtime_static_confirmation_count = 0
    runtime_static_confirmation_triggers: list[str] = []
    transitions_dir = root / "data/maps/transitions"
    for evidence_path in sorted(transitions_dir.glob("*.json")):
        try:
            runtime_evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if runtime_evidence.get("kind") != "runtime_map_transition_evidence":
            continue
        static_match = runtime_evidence.get("trigger", {}).get("static_match")
        if not static_match or not static_match.get("trigger_addr"):
            continue

        trigger_addr = static_match["trigger_addr"]
        matches = [r for r in rows if r["trigger_addr"] == trigger_addr]
        if len(matches) != 1:
            raise SystemExit(
                f"runtime confirmation {evidence_path.name} expected exactly one "
                f"static row for {trigger_addr}, found {len(matches)}"
            )
        row = matches[0]

        expected_pairs = {
            "script_pack": static_match.get("script_pack", ""),
            "destination_pack": static_match.get("destination_pack", ""),
            "destination_entry_id": static_match.get("destination_entry_id", ""),
        }
        for key, expected in expected_pairs.items():
            if expected and row[key] != expected:
                raise SystemExit(
                    f"runtime confirmation mismatch {evidence_path.name}: "
                    f"{key} static={row[key]!r} runtime={expected!r}"
                )

        destination = runtime_evidence.get("to", {})
        coord = destination.get("coordinate", {})
        if coord:
            if str(coord.get("x", "")) != str(row["destination_x"]):
                raise SystemExit(
                    f"runtime confirmation x mismatch at {trigger_addr}: "
                    f"static={row['destination_x']} runtime={coord.get('x')}"
                )
            if str(coord.get("y", "")) != str(row["destination_y"]):
                raise SystemExit(
                    f"runtime confirmation y mismatch at {trigger_addr}: "
                    f"static={row['destination_y']} runtime={coord.get('y')}"
                )

        source = runtime_evidence.get("from", {})
        source_selector = source.get("selector", {})
        row["source_config_id"] = source.get("config_id", "")
        row["source_pack"] = source.get("pack_id_hex", "")
        row["source_layout"] = source_selector.get("primary_layout", "")
        row["source_tileset"] = source_selector.get("primary_tileset", "")
        row["confidence"] = "confirmed"
        row["condition"] += (
            f"; runtime frame {runtime_evidence.get('trigger', {}).get('observed_frame')} "
            f"confirms {row['source_pack']} -> {row['destination_pack']}"
        )
        row["evidence"] += (
            f"; runtime $0305 switch at frame "
            f"{runtime_evidence.get('trigger', {}).get('observed_frame')} and "
            f"arrival coordinates ({row['destination_x']},{row['destination_y']}) "
            f"match the static destination entry"
        )
        visible_name = destination.get("human_location_name")
        if visible_name:
            row["evidence"] += f"; visible destination label={visible_name}"
        row["provenance"] += (
            f";data/maps/transitions/{evidence_path.name}"
        )
        runtime_static_confirmation_count += 1
        runtime_static_confirmation_triggers.append(trigger_addr)

    # Runtime-only edges can be projected into the catalog even when the
    # exact execution PC was not captured. These remain confirmed edges while
    # any proposed static mechanism keeps its own lower confidence in evidence.
    runtime_only_confirmation_count = 0
    for evidence_path in sorted(transitions_dir.glob("*.json")):
        try:
            runtime_evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if runtime_evidence.get("kind") != "runtime_map_transition_evidence":
            continue
        projection = runtime_evidence.get("catalog_projection")
        if not projection:
            continue
        if runtime_evidence.get("relation_status") != "confirmed_runtime_transition":
            raise SystemExit(
                f"runtime-only projection {evidence_path.name} is not a confirmed edge"
            )

        source = runtime_evidence.get("from", {})
        destination = runtime_evidence.get("to", {})
        source_selector = source.get("selector", {})
        dest_selector = destination.get("selector", {})
        coord = destination.get("coordinate", {})
        trigger = runtime_evidence.get("trigger", {})
        mechanism = runtime_evidence.get("mechanism", {})

        row = blank_row()
        row.update({
            "source_config_id": source.get("config_id", ""),
            "source_pack": source.get("pack_id_hex", ""),
            "source_layout": source_selector.get("primary_layout", ""),
            "source_tileset": source_selector.get("primary_tileset", ""),
            "trigger_type": projection.get("trigger_type", "runtime_only_transition"),
            "trigger_addr": projection.get("trigger_addr", ""),
            "destination_pack": destination.get("pack_id_hex", ""),
            "destination_config_id": destination.get("config_id", ""),
            "destination_layout": dest_selector.get("primary_layout", ""),
            "destination_tileset": dest_selector.get("primary_tileset", ""),
            "destination_variant": dest_selector.get("map_variant", ""),
            "destination_x": coord.get("x", ""),
            "destination_y": coord.get("y", ""),
            "confidence": projection.get("confidence", "confirmed"),
            "condition": (
                f"runtime frame {trigger.get('observed_frame')} confirms "
                f"{source.get('pack_id_hex', '')} -> "
                f"{destination.get('pack_id_hex', '')}; exact execution PC not observed"
            ),
            "evidence": (
                f"atomic capture hash={trigger.get('atomic_capture_sha256', '')}; "
                f"arrival selector="
                f"{dest_selector.get('primary_tileset', '')}/"
                f"{dest_selector.get('primary_layout', '')}/"
                f"{dest_selector.get('map_variant', '')}; "
                f"arrival coordinate=({coord.get('x', '')},{coord.get('y', '')}); "
                f"mechanism={mechanism.get('status', 'unresolved')}"
            ),
            "provenance": f"data/maps/transitions/{evidence_path.name}",
        })
        mechanism_addr = projection.get("mechanism_addr", "")
        if mechanism_addr:
            row["evidence"] += (
                f"; candidate mechanism writer={mechanism_addr} "
                f"(execution PC not observed)"
            )
        rows.append(row)
        runtime_only_confirmation_count += 1


    # Full raw-shape closure for opcode 0x57. Every 57 <00..0F> byte
    # shape inside a parsed VM entry is classified against the same fail-closed
    # CFG used for promotion. Non-promoted shapes with no remaining blocker and
    # no path from entry start are recorded as CFG-unreachable rather than left
    # as ambiguous candidates.
    promoted_57_addrs = {
        row["trigger_addr"] for row in rows
        if row["trigger_type"].startswith("vm_opcode_0x57")
    }
    # Promotion walks may already have memoized unrelated A0 callees. Reset
    # here so the proof count below reflects only targets needed to classify
    # the raw 0x57 corpus.
    cfg_return_memo.clear()
    cfg_return_visiting.clear()

    opcode57_raw_shape_total_count = 0
    opcode57_promoted_transition_count = 0
    opcode57_cfg_unreachable_raw_shape_count = 0
    opcode57_reachable_unpromoted_count = 0
    opcode57_unresolved_blocked_count = 0
    opcode57_reachable_unpromoted_addrs: list[str] = []
    opcode57_blocked_addrs: list[str] = []

    for entry_start, entry_end, _, _, _ in cfg_entries:
        body = rom[entry_start:entry_end]
        for target_pos in range(len(body) - 1):
            if body[target_pos] != 0x57 or body[target_pos + 1] >= 16:
                continue
            opcode57_raw_shape_total_count += 1
            addr = cpu_addr(entry_start + target_pos)
            if addr in promoted_57_addrs:
                opcode57_promoted_transition_count += 1
                continue

            reached, blockers = cfg_target_reachability(
                body, entry_start, target_pos
            )
            if reached:
                opcode57_reachable_unpromoted_count += 1
                opcode57_reachable_unpromoted_addrs.append(addr)
            elif blockers:
                opcode57_unresolved_blocked_count += 1
                opcode57_blocked_addrs.append(
                    addr + ":" + ",".join(sorted(blockers))
                )
            else:
                opcode57_cfg_unreachable_raw_shape_count += 1

    opcode57_nested_return_proof_count = sum(
        1 for ok, returned, _ in cfg_return_memo.values()
        if ok and returned
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    native_0305_writers = []
    needle = bytes.fromhex("8D 05 03")
    pos = 0
    while True:
        pos = rom.find(needle, pos)
        if pos < 0:
            break
        addr = cpu_addr(pos)
        if addr != "C4:8B7B":
            native_0305_writers.append(addr)
        pos += 1

    confidence_counts = Counter(r["confidence"] for r in rows)
    destination_pack_count = sum(bool(r["destination_pack"]) for r in rows)
    destination_config_count = sum(bool(r["destination_config_id"]) for r in rows)
    coordinate_count = sum(
        r["destination_x"] != "" and r["destination_y"] != ""
        for r in rows
    )
    event_record_count = sum(bool(r["event_record"]) for r in rows)
    event_source_count = sum(bool(r["event_sources"]) for r in rows)
    unique_destination_packs = sorted({
        r["destination_pack"] for r in rows if r["destination_pack"]
    })

    summary = {
        "schema_version": 1,
        "kind": "map_transition_candidate_catalog",
        "generated_against_git_head": current_head(root),
        "rom_sha256": sha,
        "candidate_count": len(rows),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "source_config_resolved_count": sum(bool(r["source_config_id"]) for r in rows),
        "runtime_static_confirmation_count": runtime_static_confirmation_count,
        "runtime_static_confirmation_triggers": runtime_static_confirmation_triggers,
        "runtime_only_confirmation_count": runtime_only_confirmation_count,
        "destination_pack_identified_count": destination_pack_count,
        "destination_config_resolved_count": destination_config_count,
        "destination_coordinate_resolved_count": coordinate_count,
        "event_record_crosslink_count": event_record_count,
        "event_source_crosslink_count": event_source_count,
        "additional_native_0305_writer_sites": native_0305_writers,
        "unique_destination_pack_count": len(unique_destination_packs),
        "terminal_opcode56_candidate_count": terminal_count,
        "terminal_opcode56_destination_entry_match_count": terminal_dest_entry,
        "terminal_opcode56_nonrecord0_unique_entry_match_count": terminal_nonrecord0_entry,
        "terminal_opcode56_coordinate_match_count": terminal_coord,
        "nonterminal_opcode56_coordinate_crosslink_count": nonterminal_coord,
        "nonterminal_opcode56_cfg_promoted_count": nonterminal56_cfg_promoted,
        "nonterminal_opcode56_cfg_unreachable_drop_count": nonterminal56_cfg_dropped_unreachable,
        "nonterminal_opcode56_cfg_blocked_count": nonterminal56_cfg_blocked,
        "terminal_opcode53_candidate_count": terminal53_count,
        "terminal_opcode53_destination_entry_match_count": terminal53_dest_entry,
        "terminal_opcode53_nonrecord0_unique_entry_match_count": terminal53_nonrecord0_entry,
        "terminal_opcode53_coordinate_match_count": terminal53_coord,
        "nonterminal_opcode53_coordinate_crosslink_count": nonterminal53_coord,
        "nonterminal_opcode53_cfg_promoted_count": nonterminal53_cfg_promoted,
        "nonterminal_opcode53_cfg_unreachable_drop_count": nonterminal53_cfg_dropped_unreachable,
        "nonterminal_opcode53_cfg_blocked_count": nonterminal53_cfg_blocked,
        "terminal_opcode55_candidate_count": terminal55_count,
        "terminal_opcode55_destination_entry_match_count": terminal55_dest_entry,
        "terminal_opcode55_nonrecord0_unique_entry_match_count": terminal55_nonrecord0_entry,
        "terminal_opcode55_coordinate_match_count": terminal55_coord,
        "nonterminal_opcode55_coordinate_crosslink_count": nonterminal55_coord,
        "nonterminal_opcode55_cfg_promoted_count": nonterminal55_cfg_promoted,
        "nonterminal_opcode55_cfg_unreachable_drop_count": nonterminal55_cfg_dropped_unreachable,
        "nonterminal_opcode55_cfg_blocked_count": nonterminal55_cfg_blocked,
        "nonterminal_cfg_promoted_count": (
            nonterminal56_cfg_promoted
            + nonterminal53_cfg_promoted
            + nonterminal55_cfg_promoted
        ),
        "nonterminal_cfg_unreachable_drop_count": (
            nonterminal56_cfg_dropped_unreachable
            + nonterminal53_cfg_dropped_unreachable
            + nonterminal55_cfg_dropped_unreachable
        ),
        "nonterminal_cfg_blocked_count": (
            nonterminal56_cfg_blocked
            + nonterminal53_cfg_blocked
            + nonterminal55_cfg_blocked
        ),
        "terminal_packwide_nonrecord0_unique_match_count": (
            terminal_nonrecord0_entry
            + terminal53_nonrecord0_entry
            + terminal55_nonrecord0_entry
        ),
        "terminal_unresolved_unique_entry_count": (
            (terminal_count - terminal_dest_entry)
            + (terminal53_count - terminal53_dest_entry)
            + (terminal55_count - terminal55_dest_entry)
        ),
        "terminal_unresolved_cfg_promoted_count": sum(terminal_unresolved_cfg_promoted.values()),
        "terminal_unresolved_cfg_dropped_count": sum(terminal_unresolved_cfg_dropped.values()),
        "terminal_unresolved_cfg_blocked_count": sum(terminal_unresolved_cfg_blocked.values()),
        "terminal_unresolved_cfg_promoted_by_opcode": dict(terminal_unresolved_cfg_promoted),
        "terminal_unresolved_cfg_dropped_by_opcode": dict(terminal_unresolved_cfg_dropped),
        "terminal_unresolved_cfg_blocked_by_opcode": dict(terminal_unresolved_cfg_blocked),
        "terminal_unresolved_cfg_promoted_addrs": terminal_unresolved_cfg_promoted_addrs,
        "terminal_unresolved_cfg_dropped_addrs": terminal_unresolved_cfg_dropped_addrs,
        "terminal_unresolved_cfg_blocked_addrs": terminal_unresolved_cfg_blocked_addrs,
        "terminal_opcode57_route_candidate_count": terminal57_count,
        "entry_start_opcode57_route_candidate_count": entry_start57_count,
        "cfg_reachable_opcode57_route_candidate_count": cfg_reachable57_count,
        "opcode57_raw_shape_total_count": opcode57_raw_shape_total_count,
        "opcode57_promoted_transition_count": opcode57_promoted_transition_count,
        "opcode57_cfg_unreachable_raw_shape_count": opcode57_cfg_unreachable_raw_shape_count,
        "opcode57_reachable_unpromoted_count": opcode57_reachable_unpromoted_count,
        "opcode57_reachable_unpromoted_addrs": opcode57_reachable_unpromoted_addrs,
        "opcode57_unresolved_blocked_count": opcode57_unresolved_blocked_count,
        "opcode57_blocked_addrs": opcode57_blocked_addrs,
        "opcode57_nested_return_proof_count": opcode57_nested_return_proof_count,
        "cfg_boundary_grammar": {
            "opcode_0x02_returning_operands": {
                "handler": "C4:89A5",
                "instruction_length": 2,
                "operands": ["0x17", "0x1D", "0x25", "0x2D", "0x41", "0x5C", "0x5E"],
                "policy": "caller advances before indirect call; inspected targets return through RTL",
            },
            "residual_nonterminal_closure": {
                "fixed_lengths": {
                    "0x0A": 4, "0x14": 2, "0x1A": 4, "0x42": 2,
                    "0x4A": 5, "0x4F": 5, "0x66": 4, "0x6C": 2,
                    "0x6F": 2, "0x80": 1, "0x89": 1, "0xB6": 1,
                    "0xEF": 1, "0xF0": 1
                },
                "opcode_0x3D_subtypes": "02 -> 3; 03/04/05/06 -> 2; 29 -> 5 bytes",
                "opcode_0x45": "operand1 == 0 -> 2 bytes; otherwise 5 bytes",
                "nonreturning_vm_traps": "0x7D and 0x8C both dispatch to C4:8963 BRK",
            },
            "opcode_0x2F": {
                "handler": "C4:968E",
                "instruction_length": 7,
            },
            "opcode_0x30": {
                "handler": "C4:96CC",
                "instruction_length": 6,
            },
            "opcode_0x47": {
                "handler": "C4:992F",
                "instruction_length": 5,
            },
            "opcode_0x52": {
                "handler": "C4:8B16",
                "length_rule": "operand1 < 0xFE -> 5 bytes; operand1 0xFE/0xFF -> 6 bytes",
            },
            "opcode_0x5B": {
                "handler": "C4:8FF2",
                "length_rule": (
                    "subtype operand2 1 -> 4 bytes; 2 -> 5 bytes; "
                    "3/4 -> 3 bytes; other -> 5 bytes"
                ),
            },
            "opcode_0x67": {
                "handler": "C4:924A",
                "instruction_length": 7,
            },
            "opcode_0x74": {
                "handler": "C4:9488",
                "instruction_length": 3,
            },
            "compact_A1": {
                "handler": "C4:83CD",
                "instruction_length": 2,
            },
            "compact_D0_DF": {
                "dispatcher": "C4:8108",
                "instruction_length": 3,
                "policy": "D-range dispatcher consumes two operand bytes for the audited CFG corpus",
            },
            "opcode_A0": {
                "policy": "nested call; continuation requires a blocker-free callee path with at least one return; proven 0x8C BRK trap paths terminate without fallthrough",
            },
            "opcode_B1": {
                "policy": "tail jump; same-entry target becomes a CFG edge, external target must independently return to close nested proof",
            },
        },
        "handler_findings": {
            "opcode_0x53": {
                "handler": "C4:8B3F",
                "instruction_length": 3,
                "effect": (
                    "transition wrapper; performs pre-work then JSR C4:8B6A, "
                    "therefore sharing the 0x56 destination-pack/entry core"
                ),
            },
            "opcode_0x55": {
                "handler": "C4:8B56",
                "instruction_length": 3,
                "effect": (
                    "save current primary X/Y on CPU stack; JSL 81:8244 to "
                    "restore indexed saved map state; restore current primary X/Y; "
                    "fall through to C4:8B6A destination-pack/entry transition core"
                ),
            },
            "opcode_0x56": {
                "handler": "C4:8B6A",
                "instruction_length": 3,
                "effect": (
                    "operand1 -> $15D0 and $0305; old $0305 -> $15CF; "
                    "operand2 -> $13B8/$13B9; JSL 81:837F"
                ),
            },
            "opcode_0x57": {
                "handler": "C4:8BD4",
                "instruction_length": 2,
                "guard": "$13B8 != 0",
                "effect": (
                    "operand is route index; JSL 86:8000/C6:8000; index selects "
                    "C6:8060 pointer table; route stack leaves final pack/x/y/entrance active"
                ),
            },
            "opcode_0x58": {
                "handler": "C4:8BE2",
                "instruction_length": 5,
                "guard": "$13B8 != 0",
                "effect": (
                    "four operands -> $1573/$157D/$15C3/$15C4"
                ),
            },
        },

        "unresolved_patterns": [
            "static source map/config is not inferred from script-pack identity",
            f"{terminal_count - terminal_dest_entry} reachable terminal 0x56 shapes and "
            f"{terminal53_count - terminal53_dest_entry} reachable terminal 0x53 shapes do not "
            "resolve a unique destination entry; transition pack is proven but arrival-entry "
            "semantics remain unresolved",
            *([
                f"{nonterminal56_cfg_blocked + nonterminal53_cfg_blocked + nonterminal55_cfg_blocked} "
                "non-terminal 0x53/0x55/0x56 coordinate-anchored shapes remain structural "
                "because fail-closed CFG paths still contain unresolved blockers"
            ] if (nonterminal56_cfg_blocked + nonterminal53_cfg_blocked + nonterminal55_cfg_blocked) else []),
            "destination config stays null when destination pack record0/entry1 has multiple confirmed selectors",
            "0x58 coordinate setter is promoted only at entry start or after proven two-byte opcode 0x96 prefix",
            "exact trigger/event opcode for the runtime-confirmed 0x2E -> 0x50 edge remains unidentified",
            "opcode 0x04 changes VM pack context $126E and is not promoted as a map transition by itself",
            "event-record crosslink coverage is partial; rows outside the structural frame catalog retain vm_context only",
            "native STA $0305 restore/context writers outside the explicit 0x53/0x55/0x56 destination operand grammar remain separately inventoried",
        ],
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc = """# Map transition candidate catalog

Updated: 2026-09-30

## Scope

This pass catalogs map-transition candidates only. It does not implement the
HTML viewer and does not integrate NPC or sprite data.

Canonical ROM SHA-256: {sha}
Git HEAD used for generation: {head}

## Handler-level promotion

Normal VM opcode 0x53 dispatches to C4:8B3F, performs transition pre-work,
then directly JSRs C4:8B6A. It therefore shares the same two transition
operands and three-byte advance as the 0x56 core.

Normal VM opcode 0x55 dispatches to C4:8B56. It saves the current primary
X/Y pair on the CPU stack, calls 81:8244 to restore an indexed saved map state,
restores the current primary X/Y pair, and then falls through to the C4:8B6A
transition core. It therefore also consumes destination pack/entry operands.

Normal VM opcode 0x56 dispatches to C4:8B6A and is three bytes total.
The handler copies the old global map pack $0305 to $15CF, writes operand 1
to both $15D0 and $0305, writes operand 2 to $13B8/$13B9, calls
81:837F, clears $1984, and advances by three bytes.

Normal VM opcode 0x57 dispatches to C4:8BD4. When $13B8 != 0, its one-byte
operand is passed to 86:8000, the LoROM mirror of C6:8000. C6:8000 doubles
the route index, loads a route pointer from C6:8060, builds saved map-state
nodes, and leaves the final pack/X/Y/entrance active.

Normal VM opcode 0x58 dispatches to C4:8BE2. When $13B8 != 0, its four
operands are written to primary map coordinates $1573/$157D and secondary
map coordinates $15C3/$15C4. Existing map analysis independently identifies
these fields as current-map coordinates.

## CFG boundary grammar

The fail-closed 0x57 reachability walk now carries additional handler-level
length proofs without guessing unknown instructions:

- opcode 0x02 concrete operands 0x17, 0x1D, 0x25, 0x2D, 0x41, 0x5C and
  0x5E: C4:895E advances the caller by 2 bytes before the indirect call, and
  each inspected target returns through RTL.
- residual fixed lengths proven from handlers: 0x0A=4, 0x14=2, 0x1A=4,
  0x42=2, 0x4A=5, 0x4F=5, 0x66=4, 0x6C=2, 0x6F=2, 0x80=1, 0x89=1,
  compact B6=1, E-range 0xEF=1 and 0xF0=1.
- opcode 0x3D / C4:935C: subtype 0x02 consumes 3 bytes; 0x03/0x04/0x05/0x06
  consume 2 bytes; subtype 0x29 consumes 5 bytes.
- opcode 0x45 / C4:98AC: operand1 0 consumes 2 bytes; nonzero consumes 5.
- opcodes 0x7D and 0x8C both dispatch to C4:8963, whose first instruction is
  BRK. CFG treats either as a proven non-returning trap path and never invents
  fallthrough.
- opcode 0x2F / C4:968E: six operand bytes are consumed, so 7 bytes total.
- opcode 0x30 / C4:96CC: two 16-bit operands plus one byte are consumed, so
  6 bytes total.
- opcode 0x47 / C4:992F: four operand bytes are consumed, so 5 bytes total.
- opcode 0x52 / C4:8B16: operand1 below 0xFE consumes 5 bytes total; 0xFE/0xFF
  consumes 6 bytes total.
- opcode 0x5B / C4:8FF2: subtype at operand2 selects total length
  1 -> 4 bytes, 2 -> 5 bytes, 3/4 -> 3 bytes, all other values -> 5 bytes.
- opcode 0x67 / C4:924A: helper C4:9280 consumes four operand bytes and the
  caller consumes two more, so 7 bytes total.
- opcode 0x74 / C4:9488: all paths converge at Y=3, so 3 bytes total.
- compact A1 / C4:83CD consumes one operand and advances 2 bytes total.
- compact D0..DF use the D-range dispatcher at C4:8108 and consume two
  operand bytes, so 3 bytes total for the audited corpus.
- B0/B5 terminate a substream. B2 is an unconditional rel8 branch; B3/B4 add
  branch/fallthrough edges. B1 is a tail jump and never gains synthetic
  fallthrough.
- opcode A0 is a nested VM call. Caller continuation is allowed only when a
  recursive fail-closed walk has no unresolved blockers and finds at least one
  returning route. Proven 0x8C BRK routes terminate without fallthrough.
  Same-entry B1 tail targets are followed directly; external tail targets must
  independently close as returning substreams.
""".format(sha=sha, head=summary["generated_against_git_head"])

    doc += """
## Confidence policy

- confirmed: preserved runtime-observed transition evidence.
- strong_candidate: an exact bounded VM-substream tail of
  53 <destination_pack> <destination_entry> B0,
  55 <destination_pack> <destination_entry> B0, or
  56 <destination_pack> <destination_entry> B0, with a resolved destination
  entry, or an unresolved destination entry whose source opcode boundary is
  independently CFG-reachable. Exact terminal 57 <route_index> B0 is also
  strong_candidate when route_index resolves through the proven C6:8060 route table.
- structural_candidate: an unresolved terminal or non-terminal shape retained
  only while fail-closed source CFG analysis still contains blockers.

The script-pack containing 0x53/0x55/0x56 is not automatically treated as the source map
pack. VM pack context and global map pack can differ, so static source map fields
remain blank unless independently proven.

## Counts

- total candidate rows: {candidate_count}
- confirmed: {confirmed}
- strong candidates: {strong}
- structural candidates: {structural}
- rows with source configuration: {source_configs}
- runtime-confirmed static triggers: {runtime_static}
- runtime-confirmed edges without observed trigger PC: {runtime_only}
- rows with destination pack: {dest_pack}
- rows with unique destination configuration: {dest_config}
- rows with destination X/Y: {coords}
- rows cross-linked to structural event records: {event_records}
- rows carrying existing event-source xrefs: {event_sources}
- terminal 0x56 forms: {terminal56}
- terminal 0x56 forms with matching destination entry: {terminal56_entry}
- terminal 0x56 matches resolved outside record 0: {terminal56_nonrecord0}
- terminal 0x56 forms with aligned destination 0x58 coordinates: {terminal56_coords}
- non-terminal 0x56 coordinate-crosslinked retained rows: {nonterminal56}
- non-terminal 0x56 CFG-promoted strong rows: {nonterminal56_promoted}
- non-terminal 0x56 CFG-unreachable raw shapes dropped: {nonterminal56_dropped}
- non-terminal 0x56 CFG-blocked structural rows: {nonterminal56_blocked}
- terminal 0x53 forms: {terminal53}
- terminal 0x53 forms with matching destination entry: {terminal53_entry}
- terminal 0x53 matches resolved outside record 0: {terminal53_nonrecord0}
- terminal 0x53 forms with aligned destination 0x58 coordinates: {terminal53_coords}
- non-terminal 0x53 coordinate-crosslinked retained rows: {nonterminal53}
- non-terminal 0x53 CFG-promoted strong rows: {nonterminal53_promoted}
- non-terminal 0x53 CFG-unreachable raw shapes dropped: {nonterminal53_dropped}
- non-terminal 0x53 CFG-blocked structural rows: {nonterminal53_blocked}
- terminal 0x55 forms: {terminal55}
- terminal 0x55 forms with matching destination entry: {terminal55_entry}
- terminal 0x55 matches resolved outside record 0: {terminal55_nonrecord0}
- terminal 0x55 forms with aligned destination 0x58 coordinates: {terminal55_coords}
- non-terminal 0x55 coordinate-crosslinked retained rows: {nonterminal55}
- non-terminal 0x55 CFG-promoted strong rows: {nonterminal55_promoted}
- non-terminal 0x55 CFG-unreachable raw shapes dropped: {nonterminal55_dropped}
- non-terminal 0x55 CFG-blocked structural rows: {nonterminal55_blocked}
- unmatched terminal tails CFG-promoted by source reachability: {terminal_unresolved_cfg_promoted}
- unmatched terminal tails proven CFG-unreachable and dropped: {terminal_unresolved_cfg_dropped}
- unmatched terminal tails still CFG-blocked: {terminal_unresolved_cfg_blocked}
- terminal 0x57 route-table forms: {terminal57}
- entry-start non-terminal 0x57 route-table forms: {entry_start57}
- branch-reachable non-terminal 0x57 route-table forms: {cfg_reachable57}
- all raw 57 <00..0F> shapes in parsed VM entries: {raw57_total}
- promoted 0x57 transitions among those raw shapes: {raw57_promoted}
- CFG-unreachable raw 0x57 shapes: {raw57_unreachable}
- reachable but unpromoted raw 0x57 shapes: {raw57_reachable_unpromoted}
- unresolved / blocked raw 0x57 shapes: {raw57_blocked}
- nested return targets proven by the closure walk: {raw57_nested_returns}

Opcode 0x54 is destination-indirect: it requests a saved-map-state return
rather than encoding a destination beside the opcode. Its exact terminal forms
are cataloged separately in saved_state_return_candidates.csv.

## Runtime-confirmed anchor

Three runtime anchors are now preserved.

The earlier trace confirms cfg_t07_l015_v2 / pack 0x2E transitions to
cfg_t04_l008_v2 / pack 0x50. During that transition, $0305 changes first,
then $126E/$12B4 converge to 0x50, and selector 4/8/2 becomes active.
The exact event opcode address for that interior-to-exterior edge remains unknown.

The 2026-09-29 world-map trace confirms cfg_t01_l001_v1 / pack 0x4C at
coordinate (54,236) entering pack 0x50. At frame 14455 $0305 changes
0x4C -> 0x50. The only matching terminal 0x53 static row in script pack 0x4C
is record 2 / entry 0x77 / trigger CC:0B08, targeting destination entry 0x02.
That entry's aligned 0x58 setter at CC:1C4E predicts (29,55), and runtime
coordinates become exactly (29,55) by frame 14657. The visible destination
label is 旅立ちの村. This promotes CC:0B08 from strong_candidate to confirmed.

A second 2026-09-29 trace captures the reverse edge from 旅立ちの村 /
cfg_t04_l008_v2 / pack 0x50 back to cfg_t01_l001_v1 / pack 0x4C.
During a Down atomic capture, $0305 changes 0x50 -> 0x4C at frame 14787
while the active DP pointer remains CD:FA4F. By frame 14937 selector 1/1/1 is
active under pack 0x4C at coordinate (54,237). The edge is confirmed, but the
exact execution PC was not captured. C1:8244/C1:8255 saved-map-state restore is
therefore recorded only as a strong mechanism candidate, not as the observed
trigger address.

## Important structural finding

The second transition operand used by 0x53, 0x55 and 0x56 behaves as a
destination entry selector. A pack-wide uniqueness audit across the conservative
terminal corpus finds {terminal_matches} of {terminal_total} rows with exactly
one matching parsed entry anywhere in the destination pack. Of those,
{terminal_nonrecord0_total} resolve outside record 0. No terminal row has a
duplicated matching entry ID within its destination pack. The remaining
{terminal_unresolved_total} rows have no matching parsed entry anywhere in that
pack.

Where the unique entry begins with opcode 0x58, or with the independently proven
two-byte 0x96 prefix followed by 0x58, the arrival/current-map coordinates can
be extracted without guessing.

For pack 0x50, the independently found 0x56 shapes using entry IDs 0x04, 0x0B
and 0x10 cross-link to unique entries carrying 0x58 coordinate setters,
including coordinates (29,55) and (34,49).

The non-record0 extension is especially visible for destination pack 0xF7:
terminal 0x53 rows from packs 0xF3/0xF4 select entry IDs 0x02..0x07 and
0x0C..0x14. Each requested ID exists exactly once in pack 0xF7, in records
outside record 0, and the matched entries carry aligned 0x58 arrival setters.
The same unique non-record0 pattern resolves destination entries 0x0B/0x0C/0x0D
in pack 0xEE and entry 0x07 in pack 0xF0.

Opcode 0x57 forms a second transition grammar: the operand is a native route
index rather than a destination pack. Two exact terminal forms are currently
proven, route index 3 ending at pack 0x50 / (39,37) / entrance 0x02 and route
index 14 ending at pack 0x6A / (88,20) / entrance 0x02.

Eight additional non-terminal forms are promoted because 0x57 is byte 0 of the
parsed entry, independently proving the instruction boundary. All eight are
immediately followed by aligned opcode 0x58, so the route table supplies the
destination pack while 0x58 supplies the effective X/Y and secondary X/Y.
Seven further non-terminal 0x57 instructions are reachable from parsed entry
starts through the fail-closed CFG using proven B2/B3/B4 branch semantics and
independently bounded opcode lengths.

- pack 0x4E / record 0 / entry 0x03: CC:1916, route index 0x01. The path is
  D0 B9 13, D5 B8 13, E0, 96 00, then 57 01. The immediately following
  58 07 03 07 03 establishes effective coordinates (7,3).
- pack 0xDD / record 1 / entry 0x79: CD:B652, CD:B664 and CD:B676 with route
  indices 0x06, 0x07 and 0x08.
- the same pack/record/entry later reaches CD:B68D, CD:B6A1 and CD:B6B5 with
  route indices 0x09, 0x0A and 0x0B. Each is immediately preceded by opcode
  02 41. That opcode resolves to routine 81:EC60, while C4:895E advances the
  caller by two bytes before the indirect call and 81:EC60 returns through RTL,
  proving continuation to the following 0x57 instructions.

The remaining raw 0x57-shaped bytes are now fully closed by the same
fail-closed CFG. Across all parsed VM entries there are {raw57_total} raw
57 <00..0F> shapes: {raw57_promoted} are promoted transitions and the other
{raw57_unreachable} are unreachable from their parsed entry starts under the
proven grammar. There are {raw57_reachable_unpromoted} reachable-but-unpromoted
and {raw57_blocked} unresolved/blocked shapes. The earlier raw 0x57 backlog is
therefore closed rather than merely deferred.

## Deliberate non-promotions

Opcode 0x04 is a proven VM pack-context switch for $126E, but it is not treated
as a global map transition because it does not itself write $0305.

Raw 0x53/0x55/0x56-shaped bytes outside the bounded policy are not cataloged.
Non-terminal shapes first require a destination-entry/0x58 coordinate cross-link.
The fail-closed CFG then promotes reachable opcode boundaries to strong candidates,
drops coordinate-anchored raw shapes that are provably unreachable from the parsed
entry start, and retains only blocker-bearing shapes as structural candidates.

## Related state fields

- $0305 is the global current-map pack field written by the C4:8B6A core used by opcodes 0x53, 0x55 and 0x56.
- $126E is VM pack context. Opcode 0x04 changes $126E, so it is useful context
  but is not sufficient evidence for a global map transition.
- $12B4 is the resolved current source family/pack context used by source
  selection. In the confirmed runtime transition it converges with $126E after
  $0305 has already changed.
- normal opcode 0x50 writes primary selector state $139C/$139E/$139B
  (tileset/layout/variant).
- normal opcode 0x51 writes secondary selector state $139D/$139F.
- the destination configuration columns are therefore joined from the existing
  confirmed 0x50 selector catalog, not inferred from the transition operands.
- data/events/event_record_frame_catalog.csv is range-joined against each
  trigger address. Matching record IDs are stored in event_record.
- data/events/event_source_crosslink.csv is then joined by record ID and stored
  in event_sources. Rows outside the structural frame catalog keep event_record
  blank while vm_context preserves script pack/record/entry without guessing.

## Additional native $0305 writer inventory

Outside C4:8B7B inside opcode 0x56, exact STA-absolute $0305 byte patterns occur
at: {native_writers}

These sites are separately inventoried because some are save/restore or
temporary-context writes rather than explicit destination operands. Runtime-only
edges may still use them as mechanism candidates without claiming the execution
PC was observed.

## Reproducible outputs

- data/maps/transitions/map_transition_candidates.csv
- data/maps/transitions/map_transition_candidates_summary.json
- docs/analysis/map_transition_candidate_catalog.md
- tools/python/catalog_map_transition_candidates.py
- data/maps/transitions/world_pack4c_to_pack50_entry02_20260929.json
- data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json
- data/maps/transitions/saved_state_return_candidates.csv
- data/maps/transitions/saved_state_return_summary.json
- docs/analysis/map_saved_state_return_catalog.md
- tools/python/catalog_saved_state_return_candidates.py

## Remaining blockers

""".format(
        candidate_count=summary["candidate_count"],
        confirmed=confidence_counts.get("confirmed", 0),
        strong=confidence_counts.get("strong_candidate", 0),
        structural=confidence_counts.get("structural_candidate", 0),
        source_configs=summary["source_config_resolved_count"],
        runtime_static=runtime_static_confirmation_count,
        runtime_only=runtime_only_confirmation_count,
        dest_pack=destination_pack_count,
        dest_config=destination_config_count,
        coords=coordinate_count,
        event_records=event_record_count,
        event_sources=event_source_count,
        native_writers=", ".join(native_0305_writers),
        terminal56=terminal_count,
        terminal56_entry=terminal_dest_entry,
        terminal56_nonrecord0=terminal_nonrecord0_entry,
        terminal56_coords=terminal_coord,
        nonterminal56=nonterminal_coord,
        nonterminal56_promoted=nonterminal56_cfg_promoted,
        nonterminal56_dropped=nonterminal56_cfg_dropped_unreachable,
        nonterminal56_blocked=nonterminal56_cfg_blocked,
        terminal53=terminal53_count,
        terminal53_entry=terminal53_dest_entry,
        terminal53_nonrecord0=terminal53_nonrecord0_entry,
        terminal53_coords=terminal53_coord,
        nonterminal53=nonterminal53_coord,
        nonterminal53_promoted=nonterminal53_cfg_promoted,
        nonterminal53_dropped=nonterminal53_cfg_dropped_unreachable,
        nonterminal53_blocked=nonterminal53_cfg_blocked,
        terminal55=terminal55_count,
        terminal55_entry=terminal55_dest_entry,
        terminal55_nonrecord0=terminal55_nonrecord0_entry,
        terminal55_coords=terminal55_coord,
        nonterminal55=nonterminal55_coord,
        nonterminal55_promoted=nonterminal55_cfg_promoted,
        nonterminal55_dropped=nonterminal55_cfg_dropped_unreachable,
        nonterminal55_blocked=nonterminal55_cfg_blocked,
        terminal_unresolved_cfg_promoted=sum(terminal_unresolved_cfg_promoted.values()),
        terminal_unresolved_cfg_dropped=sum(terminal_unresolved_cfg_dropped.values()),
        terminal_unresolved_cfg_blocked=sum(terminal_unresolved_cfg_blocked.values()),
        terminal57=terminal57_count,
        entry_start57=entry_start57_count,
        cfg_reachable57=cfg_reachable57_count,
        raw57_total=opcode57_raw_shape_total_count,
        raw57_promoted=opcode57_promoted_transition_count,
        raw57_unreachable=opcode57_cfg_unreachable_raw_shape_count,
        raw57_reachable_unpromoted=opcode57_reachable_unpromoted_count,
        raw57_blocked=opcode57_unresolved_blocked_count,
        raw57_nested_returns=opcode57_nested_return_proof_count,
        terminal_matches=terminal_dest_entry + terminal53_dest_entry + terminal55_dest_entry,
        terminal_total=terminal_count + terminal53_count + terminal55_count,
        terminal_nonrecord0_total=(
            terminal_nonrecord0_entry
            + terminal53_nonrecord0_entry
            + terminal55_nonrecord0_entry
        ),
        terminal_unresolved_total=(
            (terminal_count - terminal_dest_entry)
            + (terminal53_count - terminal53_dest_entry)
            + (terminal55_count - terminal55_dest_entry)
        ),
    )

    for item in summary["unresolved_patterns"]:
        doc += "- " + item + "\n"
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(doc, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
