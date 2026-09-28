#!/usr/bin/env python3
"""Catalog structurally bounded Shinmomo map-selector candidates.

This parser is intentionally conservative.

It uses the CA:C000 master pack table and pack-local 16-bit record pointer
tables, including the four packs whose pointers wrap into the next bank. The
full 0x14..0xF9 corpus contains 4,324 bounded VM records after one known
pointer/table blob is excluded. Within records that expose the proven
entry/substream header grammar,

    [entry_id:1][substream_ptr16:2] ... 00

it catalogs normal-map-shaped opcode 0x50 commands whose operands satisfy the
ROM-side map-loader table cardinalities and the confirmed $139B variant range.

Important: opcode >= 0x50 is dispatched through a different bank-82 table when
$1398 != 0. Therefore rows outside the already confirmed setup signature remain
"structurally strong candidates", not unconditional runtime semantics.

No ROM payload or decoded map grid is written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

CA_TABLE_FILE = 0x0AC000
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9

# These packs demonstrate the 16-bit record-pointer bank-wrap rule.
KNOWN_CROSS_BANK_PACKS = {0x15, 0x48, 0x9E, 0xF2}

# Family 0x14 record 0 is a large pointer/table blob, not a VM record.
EXCLUDED_NON_VM_RECORDS = {(0x14, 0)}

CONFIRMED_SETUP_SIGNATURE = bytes.fromhex("10 0A 10 0B 11 09")

# State-0 record0/entry1 promotion proof.
#
# 81:98D1 seeds entry_id 0x01 and explicitly writes $035F=2 immediately
# before JSL $84:8508 / JSL $84:858D.  For the common aligned prefix family,
# only these four normal opcodes occur before the candidate 0x50.
#
# Static call-graph analysis has bounded these handlers/callees as not writing
# $035F/$1398/$1399 and not re-entering C0:C9E7.
STATE0_PREFIX_SAFE_LENGTHS = {
    0x96: 2,
    0x10: 2,
    0x11: 2,
    0x33: 4,
}
STATE0_DESCRIPTOR_INDEX = 2
STATE0_DESCRIPTOR_EXPECTED_PTR = 0x0850
STATE0_SAFE_B910_TARGETS = {0xB924, 0xB944}


def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | (addr & 0xFFFF)


def cpu_from_file(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def u16_file(rom: bytes, off: int) -> int:
    return rom[off] | (rom[off + 1] << 8)


def u24_file(rom: bytes, off: int) -> int:
    return rom[off] | (rom[off + 1] << 8) | (rom[off + 2] << 16)


def read_pack_root(rom: bytes, pack_id: int) -> tuple[int, int, int]:
    off = CA_TABLE_FILE + pack_id * 3
    lo, hi, bank = rom[off : off + 3]
    addr = lo | (hi << 8)
    return bank, addr, file_from_cpu(bank, addr)


def parse_pack(rom: bytes, pack_id: int) -> dict | None:
    """Parse a pack-local 16-bit pointer table, allowing bank wrap.

    Pointer words remain 16-bit when a pack crosses a 64 KiB boundary. A
    decrease in the pointer word advances the implied bank by one.
    """
    bank, addr, start = read_pack_root(rom, pack_id)
    next_bank, next_addr, end = read_pack_root(rom, pack_id + 1)

    first_ptr16 = u16_file(rom, start)
    first_bank = bank + (1 if first_ptr16 < addr else 0)
    first = file_from_cpu(first_bank, first_ptr16)

    delta = first - start
    if delta < 4 or (delta - 4) % 2:
        return None
    count = (delta - 4) // 2
    if count <= 0:
        return None

    ptr16s = [u16_file(rom, start + 2 * i) for i in range(count)]
    trailer = rom[start + count * 2 : start + count * 2 + 4]
    if trailer != bytes([0x00, 0x00, 0x00, pack_id]):
        return None

    ptrs = []
    current_bank = bank
    for i, ptr16 in enumerate(ptr16s):
        if (i == 0 and ptr16 < addr) or (
            i > 0 and ptr16 < ptr16s[i - 1]
        ):
            current_bank += 1
        ptrs.append(file_from_cpu(current_bank, ptr16))

    if ptrs[0] != first:
        return None
    if any(ptrs[i] >= ptrs[i + 1] for i in range(len(ptrs) - 1)):
        return None
    if not all(start < p < end for p in ptrs):
        return None

    records = []
    for record_index, record_start in enumerate(ptrs):
        record_end = ptrs[record_index + 1] if record_index + 1 < len(ptrs) else end
        records.append(
            {
                "pack_id": pack_id,
                "record_index": record_index,
                "start": record_start,
                "end": record_end,
            }
        )

    return {
        "pack_id": pack_id,
        "bank": bank,
        "next_bank": next_bank,
        "crosses_bank": bank != next_bank,
        "start": start,
        "end": end,
        "records": records,
    }


def parse_record_header(rom: bytes, record: dict) -> dict | None:
    """Parse [entry_id][ptr16]...00 and require ordered in-record targets."""
    start = record["start"]
    end = record["end"]
    p = start
    entries = []

    while p < end and len(entries) < 128:
        entry_id = rom[p]
        if entry_id == 0:
            header_end = p + 1
            if not entries:
                return None
            targets = [e["start"] for e in entries]
            if not all(header_end <= t < end for t in targets):
                return None
            if any(targets[i] >= targets[i + 1] for i in range(len(targets) - 1)):
                return None
            for i, entry in enumerate(entries):
                entry["end"] = entries[i + 1]["start"] if i + 1 < len(entries) else end
            return {
                "header_end": header_end,
                "entries": entries,
            }

        if p + 2 >= end:
            return None
        ptr16 = rom[p + 1] | (rom[p + 2] << 8)
        target = (start & ~0xFFFF) | ptr16
        if target < start:
            target += 0x10000
        entries.append(
            {
                "entry_id": entry_id,
                "header_field": p,
                "start": target,
            }
        )
        p += 3

    return None


def tileset_pointer(rom: bytes, tileset_id: int) -> int:
    off = file_from_cpu(0xCE, 0x2000 + (tileset_id - 1) * 2)
    return u16_file(rom, off)


def layout_pointer(rom: bytes, layout_id: int) -> int:
    off = file_from_cpu(0xCF, 0x2000) + (layout_id - 1) * 3
    return u24_file(rom, off)


def layout_meta(rom: bytes, layout_id: int) -> dict:
    ptr = layout_pointer(rom, layout_id)
    bank = (ptr >> 16) & 0xFF
    addr = ptr & 0xFFFF
    off = file_from_cpu(bank, addr)
    flags = rom[off]
    width = rom[off + 1]
    height = rom[off + 2]
    cell_count = rom[off + 3] | (rom[off + 4] << 8)
    return {
        "layout_ptr": f"{bank:02X}:{addr:04X}",
        "layout_flags": f"0x{flags:02X}",
        "layout_width_chunks": width,
        "layout_height_chunks": height,
        "layout_cell_count": cell_count,
        "logical_width_metatiles": width * 16,
        "logical_height_metatiles": height * 16,
    }


def validate_state0_prefix_anchors(rom: bytes) -> None:
    """Fail closed if any static anchor behind the state-0 proof changes."""
    helper = file_from_cpu(0xC1, 0x98D1)
    expected = bytes.fromhex(
        "9C 07 03 A9 02 8D 5F 03 9C 19 16 AD 05 03 "
        "22 08 85 84 A9 01 22 8D 85 84 60"
    )
    got = rom[helper : helper + len(expected)]
    if got != expected:
        raise SystemExit(
            "state0 entry1 helper anchor changed at C1:98D1: "
            + got.hex(" ")
        )

    # B7A7 selects a C3 descriptor base through BAAC[2*$035F].
    baac = file_from_cpu(0xC0, 0xBAAC)
    ptr = u16_file(rom, baac + 2 * STATE0_DESCRIPTOR_INDEX)
    if ptr != STATE0_DESCRIPTOR_EXPECTED_PTR:
        raise SystemExit(
            f"unexpected state0 descriptor base: C3:{ptr:04X}"
        )

    # B910's descriptor-indexed targets used by this proof are exact short
    # routines: B924 -> C07F, B944 -> BD28.
    b924 = file_from_cpu(0xC0, 0xB924)
    if rom[b924 : b924 + 8] != bytes.fromhex("AD 24 11 22 7F C0 80 60"):
        raise SystemExit("unexpected B910 target body at C0:B924")
    b944 = file_from_cpu(0xC0, 0xB944)
    if rom[b944 : b944 + 5] != bytes.fromhex("22 28 BD 80 60"):
        raise SystemExit("unexpected B910 target body at C0:B944")


def state0_prefix_mode_safe(
    rom: bytes,
    record_index: int,
    entry_id: int,
    stream_start: int,
    target: int,
) -> tuple[bool, str]:
    """Prove the common state-0 prefix family remains in normal mode.

    This is intentionally much narrower than the general prefix decoder.
    It accepts only record0/entry1 and only opcode 96/10/11/33.  For every
    10/33 descriptor operation, it resolves the $035F=2 descriptor through
    C3:0850 and requires B910 to land on the already-cleared B924/B944
    routines.
    """
    if record_index != 0 or entry_id != 0x01:
        return False, ""

    p = stream_start
    b910_targets: set[int] = set()
    descriptor_base = file_from_cpu(0xC3, STATE0_DESCRIPTOR_EXPECTED_PTR)
    b910_table = file_from_cpu(0xC0, 0xB91C)

    while p < target:
        op = rom[p]
        length = STATE0_PREFIX_SAFE_LENGTHS.get(op)
        if length is None or p + length > target:
            return False, ""

        descriptor_id = None
        if op == 0x10:
            descriptor_id = rom[p + 1]
        elif op == 0x33:
            descriptor_id = rom[p + 3]

        if descriptor_id is not None:
            if descriptor_id == 0:
                return False, ""
            descriptor = descriptor_base + (descriptor_id - 1) * 8
            if descriptor + 8 > len(rom):
                return False, ""
            last = rom[descriptor + 7]
            x = (last & 0xF0) >> 3
            # $1123 is an even byte offset into the B910 indirect table.
            if x & 1:
                return False, ""
            table_entry = b910_table + x
            if table_entry + 2 > len(rom):
                return False, ""
            call_target = u16_file(rom, table_entry)
            if call_target not in STATE0_SAFE_B910_TARGETS:
                return False, ""
            b910_targets.add(call_target)

        p += length

    if p != target:
        return False, ""

    label = ",".join(f"C0:{x:04X}" for x in sorted(b910_targets))
    return True, label


def special_interpretation_status(rom: bytes, layout_id: int) -> str:
    """Classify the opcode that follows a bank82-special 0x50 interpretation.

    The special 0x50 handler advances the VM pointer by exactly two bytes via
    C4:9BC5 -> C4:8410. Therefore the normal-map-shaped byte at +2 (layout_id)
    would become the next opcode under special mode.

    - low opcodes use the normal C4 dispatch table even when $1398 != 0;
    - 0x50..0x92 use the bounded bank82 special table;
    - >0x92 is outside the proven bank82 table;
    - low entries routed to C4:8963 hit the BRK guard.
    """
    if layout_id < 0x50:
        dispatch = file_from_cpu(0xC4, 0x87D4 + layout_id * 2)
        handler = u16_file(rom, dispatch)
        if handler == 0x8963:
            return "invalid_normal_brk"
        return "possible_normal_low_opcode"
    if layout_id <= 0x92:
        return "possible_bank82_special_opcode"
    return "invalid_bank82_special_range"


def build_corpus(rom: bytes) -> tuple[list[dict], dict]:
    packs = []
    rejected = []
    for pack_id in range(FIRST_REAL_PACK, LAST_REAL_PACK + 1):
        parsed = parse_pack(rom, pack_id)
        if parsed is None:
            rejected.append(pack_id)
        else:
            packs.append(parsed)

    records = []
    for pack in packs:
        records.extend(pack["records"])

    # This one is independently identified as a pointer/table blob.
    records = [
        r for r in records
        if (r["pack_id"], r["record_index"]) not in EXCLUDED_NON_VM_RECORDS
    ]

    valid_header_count = 0
    substream_count = 0
    for record in records:
        header = parse_record_header(rom, record)
        record["header"] = header
        if header:
            valid_header_count += 1
            substream_count += len(header["entries"])

    summary = {
        "parsed_pack_count": len(packs),
        "parse_failure_pack_ids": [f"0x{x:02X}" for x in rejected],
        "cross_bank_pack_ids": [
            f"0x{x['pack_id']:02X}" for x in packs if x["crosses_bank"]
        ],
        "known_cross_bank_pack_ids": [f"0x{x:02X}" for x in sorted(KNOWN_CROSS_BANK_PACKS)],
        "bounded_vm_record_count": len(records),
        "excluded_non_vm_records": [
            {"pack_id": f"0x{p:02X}", "record_index": r}
            for p, r in sorted(EXCLUDED_NON_VM_RECORDS)
        ],
        "records_with_valid_entry_header": valid_header_count,
        "valid_substream_entries": substream_count,
    }
    return records, summary


def candidate_rows(rom: bytes, records: list[dict]) -> tuple[list[dict], list[dict]]:
    primary = []
    all_secondary_shape = []

    for record in records:
        header = record["header"]
        if not header:
            continue

        pack_id = record["pack_id"]
        record_index = record["record_index"]
        record_start = record["start"]
        record_end = record["end"]

        for entry in header["entries"]:
            entry_id = entry["entry_id"]
            stream_start = entry["start"]
            stream_end = entry["end"]

            # Primary normal-map-shaped 0x50.
            for p in range(stream_start, max(stream_start, stream_end - 3)):
                if rom[p] != 0x50 or p + 4 > stream_end:
                    continue
                tileset_id = rom[p + 1]
                layout_id = rom[p + 2]
                variant = rom[p + 3]
                if not (1 <= tileset_id <= 60):
                    continue
                if not (1 <= layout_id <= 203):
                    continue
                # C0:C6FD is 1-based and wrappers feed 1/2/3.
                if not (1 <= variant <= 3):
                    continue

                confirmed_signature = (
                    p >= stream_start + len(CONFIRMED_SETUP_SIGNATURE)
                    and rom[p - len(CONFIRMED_SETUP_SIGNATURE) : p]
                    == CONFIRMED_SETUP_SIGNATURE
                )
                special_status = special_interpretation_status(rom, layout_id)
                special_impossible = special_status.startswith("invalid_")
                state0_safe, state0_b910_targets = state0_prefix_mode_safe(
                    rom,
                    record_index,
                    entry_id,
                    stream_start,
                    p,
                )
                # Count this proof as a promotion only when earlier independent
                # proofs did not already confirm the row.
                state0_prefix_promoted = (
                    state0_safe
                    and not confirmed_signature
                    and not special_impossible
                )
                normal_mode_confirmed = (
                    confirmed_signature
                    or special_impossible
                    or state0_prefix_promoted
                )
                if confirmed_signature and special_impossible:
                    evidence = "confirmed_setup_signature_and_special_parse_impossible"
                elif confirmed_signature:
                    evidence = "confirmed_setup_signature"
                elif special_impossible:
                    evidence = "confirmed_normal_special_parse_impossible"
                elif state0_prefix_promoted:
                    evidence = "confirmed_normal_state0_safe_prefix"
                else:
                    evidence = "strong_structural_candidate_mode_gate_unresolved"

                tptr = tileset_pointer(rom, tileset_id)
                meta = layout_meta(rom, layout_id)

                row = {
                    "pack_id_dec": pack_id,
                    "pack_id_hex": f"0x{pack_id:02X}",
                    "record_index": record_index,
                    "record_start": cpu_from_file(record_start),
                    "record_end_exclusive": cpu_from_file(record_end),
                    "entry_id_dec": entry_id,
                    "entry_id_hex": f"0x{entry_id:02X}",
                    "substream_start": cpu_from_file(stream_start),
                    "substream_end_exclusive": cpu_from_file(stream_end),
                    "command_addr": cpu_from_file(p),
                    "opcode": "0x50",
                    "primary_tileset_id": tileset_id,
                    "primary_tileset_ptr": f"CE:{tptr:04X}",
                    "primary_layout_id": layout_id,
                    "map_variant": variant,
                    "evidence_class": evidence,
                    "confirmed_setup_signature": confirmed_signature,
                    "special_interpretation_status": special_status,
                    "special_interpretation_impossible": special_impossible,
                    "state0_prefix_mode_safe": state0_safe,
                    "state0_prefix_promoted": state0_prefix_promoted,
                    "state0_prefix_b910_targets": state0_b910_targets,
                    "normal_mode_confirmed": normal_mode_confirmed,
                    **meta,
                    "immediate_secondary": False,
                    "secondary_command_addr": "",
                    "secondary_tileset_id": "",
                    "secondary_tileset_ptr": "",
                    "secondary_layout_id": "",
                    "secondary_layout_ptr": "",
                }

                # Immediate 0x51 is structurally compelling because normal 0x50
                # consumes exactly four bytes.
                if p + 7 <= stream_end and rom[p + 4] == 0x51:
                    st = rom[p + 5]
                    sl = rom[p + 6]
                    if 1 <= st <= 60 and 1 <= sl <= 203:
                        sptr = tileset_pointer(rom, st)
                        lptr = layout_pointer(rom, sl)
                        row.update(
                            {
                                "immediate_secondary": True,
                                "secondary_command_addr": cpu_from_file(p + 4),
                                "secondary_tileset_id": st,
                                "secondary_tileset_ptr": f"CE:{sptr:04X}",
                                "secondary_layout_id": sl,
                                "secondary_layout_ptr": f"{(lptr >> 16) & 0xFF:02X}:{lptr & 0xFFFF:04X}",
                            }
                        )
                primary.append(row)

            # Keep range-plausible standalone 0x51 rows separately. These are
            # mode-ambiguous because $1398 can route the same opcode to bank82.
            for p in range(stream_start, max(stream_start, stream_end - 2)):
                if rom[p] != 0x51 or p + 3 > stream_end:
                    continue
                st = rom[p + 1]
                sl = rom[p + 2]
                if not (1 <= st <= 60 and 1 <= sl <= 203):
                    continue
                sptr = tileset_pointer(rom, st)
                lptr = layout_pointer(rom, sl)
                all_secondary_shape.append(
                    {
                        "pack_id_dec": pack_id,
                        "pack_id_hex": f"0x{pack_id:02X}",
                        "record_index": record_index,
                        "record_start": cpu_from_file(record_start),
                        "record_end_exclusive": cpu_from_file(record_end),
                        "entry_id_dec": entry_id,
                        "entry_id_hex": f"0x{entry_id:02X}",
                        "substream_start": cpu_from_file(stream_start),
                        "substream_end_exclusive": cpu_from_file(stream_end),
                        "command_addr": cpu_from_file(p),
                        "opcode": "0x51",
                        "secondary_tileset_id": st,
                        "secondary_tileset_ptr": f"CE:{sptr:04X}",
                        "secondary_layout_id": sl,
                        "secondary_layout_ptr": f"{(lptr >> 16) & 0xFF:02X}:{lptr & 0xFFFF:04X}",
                        "evidence_class": "mode_ambiguous_secondary_shape",
                    }
                )

    paired_primary_by_secondary = {
        r["secondary_command_addr"]: r
        for r in primary
        if r["immediate_secondary"]
    }
    for row in all_secondary_shape:
        parent = paired_primary_by_secondary.get(row["command_addr"])
        if parent is None:
            continue
        if parent["normal_mode_confirmed"]:
            row["evidence_class"] = "confirmed_normal_immediate_secondary_pair"
        else:
            row["evidence_class"] = "strong_immediate_secondary_pair_mode_gate_unresolved"

    return primary, all_secondary_shape


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("data/maps/selectors"))
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM SHA-256: {sha}")

    validate_state0_prefix_anchors(rom)
    records, corpus = build_corpus(rom)
    primary, secondary = candidate_rows(rom, records)

    signature_confirmed = [r for r in primary if r["confirmed_setup_signature"]]
    special_impossible = [r for r in primary if r["special_interpretation_impossible"]]
    state0_prefix_safe = [r for r in primary if r["state0_prefix_mode_safe"]]
    state0_prefix_promoted = [r for r in primary if r["state0_prefix_promoted"]]
    normal_confirmed = [r for r in primary if r["normal_mode_confirmed"]]
    unresolved_primary = [r for r in primary if not r["normal_mode_confirmed"]]
    paired = [r for r in primary if r["immediate_secondary"]]
    secondary_confirmed = [
        r for r in secondary
        if r["evidence_class"] == "confirmed_normal_immediate_secondary_pair"
    ]
    secondary_strong_unresolved = [
        r for r in secondary
        if r["evidence_class"] == "strong_immediate_secondary_pair_mode_gate_unresolved"
    ]
    secondary_ambiguous = [
        r for r in secondary
        if r["evidence_class"] == "mode_ambiguous_secondary_shape"
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "primary_map_selector_catalog.csv", primary)
    write_csv(args.out_dir / "secondary_map_selector_candidates.csv", secondary)
    write_csv(
        args.out_dir / "state0_safe_prefix_promotions.csv",
        state0_prefix_promoted,
    )

    summary = {
        "schema_version": 1,
        "kind": "derived_map_selector_catalog",
        "rom_sha256": sha,
        "policy": "Addresses/IDs/derived metadata only; no ROM payloads.",
        "normal_vs_special_dispatch_caveat": (
            "For opcode >= 0x50, C4:87A2 routes to bank82 special dispatch when "
            "$1398 != 0. The bank82-special 0x50 consumes two bytes; therefore "
            "its next opcode would be the normal-map candidate's layout_id byte. "
            "Rows whose layout_id is outside the proven special range or maps to "
            "the C4 BRK handler cannot be interpreted as special 0x50 and are "
            "promoted to confirmed normal mode. In addition, a narrowly proven "
            "state0 record0/entry1 prefix family is promoted when its prefix uses "
            "only 96/10/11/33, the state0 helper seeds $035F=2, and every "
            "descriptor-resolved B910 indirect target is one of the cleared "
            "B924/B944 routines. Other rows remain mode-gate unresolved."
        ),
        "corpus": corpus,
        "primary": {
            "strong_shape_total": len(primary),
            "confirmed_setup_signature": len(signature_confirmed),
            "confirmed_special_interpretation_impossible": len(special_impossible),
            "state0_prefix_mode_safe_rows": len(state0_prefix_safe),
            "newly_promoted_state0_safe_prefix": len(state0_prefix_promoted),
            "state0_prefix_b910_targets": sorted(
                {
                    target
                    for r in state0_prefix_promoted
                    for target in r["state0_prefix_b910_targets"].split(",")
                    if target
                }
            ),
            "confirmed_normal_union": len(normal_confirmed),
            "mode_gate_unresolved": len(unresolved_primary),
            "special_interpretation_status_counts": {
                k: v
                for k, v in sorted(
                    Counter(r["special_interpretation_status"] for r in primary).items()
                )
            },
            "unique_configurations": len(
                {
                    (
                        r["primary_tileset_id"],
                        r["primary_layout_id"],
                        r["map_variant"],
                    )
                    for r in primary
                }
            ),
            "distinct_tileset_ids": len({r["primary_tileset_id"] for r in primary}),
            "distinct_layout_ids": len({r["primary_layout_id"] for r in primary}),
            "variant_counts": {
                str(k): v
                for k, v in sorted(Counter(r["map_variant"] for r in primary).items())
            },
            "families_with_candidates": len({r["pack_id_dec"] for r in primary}),
            "immediate_secondary_pair_rows": len(paired),
        },
        "secondary": {
            "range_plausible_substream_rows": len(secondary),
            "immediate_pair_rows_total": len(paired),
            "confirmed_normal_immediate_pairs": len(secondary_confirmed),
            "strong_immediate_pairs_mode_gate_unresolved": len(secondary_strong_unresolved),
            "mode_ambiguous_standalone_rows": len(secondary_ambiguous),
            "unique_immediate_pair_configurations": len(
                {
                    (
                        r["primary_tileset_id"],
                        r["primary_layout_id"],
                        r["map_variant"],
                        r["secondary_tileset_id"],
                        r["secondary_layout_id"],
                    )
                    for r in paired
                }
            ),
        },
        "stable_interior": {
            "expected_primary_command": "50 07 0F 02",
            "confirmed_addresses": ["CB:DE70", "CC:5391", "CE:0F2B"],
            "catalog_matches": [
                r["command_addr"]
                for r in primary
                if r["primary_tileset_id"] == 7
                and r["primary_layout_id"] == 15
                and r["map_variant"] == 2
            ],
        },
        "outputs": [
            "primary_map_selector_catalog.csv",
            "secondary_map_selector_candidates.csv",
            "state0_safe_prefix_promotions.csv",
            "primary_map_selector_summary.json",
        ],
    }

    (args.out_dir / "primary_map_selector_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
