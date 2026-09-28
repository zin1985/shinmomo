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
    0x08: 4,
    0x2D: 2,
    0xA3: 2,
    # E-range expression operators are intercepted by the scheduler. The
    # E dispatcher advances the stream by one byte before executing the
    # operator handler. E1 and E8 are mode-safe boolean/comparison operators
    # needed by the residual state0 map-entry CFG.
    0xE0: 1,
    0xE1: 1,
    0xE7: 1,
    0xE8: 1,
    # 0x15 is allowed only when it is the final instruction before the
    # candidate 0x50; see state0_prefix_mode_safe().
    0x15: 3,
}
STATE0_SAFE_BRANCH_OPS = {0xB2, 0xB3, 0xB4}
STATE0_DESCRIPTOR_INDEX = 2
STATE0_DESCRIPTOR_EXPECTED_PTR = 0x0850
STATE0_SAFE_B910_TARGETS = {0xB924, 0xB944}

# Concrete nested A0 call targets reached by the final four state0 record0/entry1
# selector prefixes.  Each target is also a proven pack-record substream start.
# Values are (end_bank, end_addr, SHA-256 of [start,end)).
STATE0_SAFE_A0_SUBSTREAMS = {
    (0xCC, 0x1828): (
        0xCC, 0x1888,
        "c47a70f91a033716d951dcc0ba289414b76b3b0002237d6358e6958d391b79fa",
    ),
    (0xCD, 0xF037): (
        0xCD, 0xF04C,
        "1ac93076e9caf622876239336365f449296357b2c9d7eb59d2677acbd9d86c40",
    ),
    (0xCD, 0x6C9C): (
        0xCD, 0x6CBD,
        "e9d588229eb3b63de36b85bd5392c4f98adc792ee74ae1818747b23cdf19eb4b",
    ),
    (0xCD, 0xE34F): (
        0xCD, 0xE369,
        "62d30200defccae0d1ce282f9b7b7bf7781df20f978f7f582765b7cfb6c7a0b4",
    ),
}

# Normal opcode 0x02 dispatches through a 24-bit routine table.  Only these
# operand/target pairs occur in the approved A0 substreams.
STATE0_SAFE_OP02_TARGETS = {
    0x06: (
        0x84, 0xCC8A, 0xCC9D,
        "45e2a30dcd6e700c1b978a5747fc7583e7aafa8b1d7e09d89c107d5c42aed71b",
    ),
    0x12: (
        0x83, 0xBB7A, 0xBBAB,
        "ebe1aae4eba1b276e2ec315a2394a53ecc506fe85a1ef045d1cb546a70db7b1f",
    ),
    0x1C: (
        0x83, 0xADE2, 0xAE1C,
        "ff79974456430cb90f21bbb0727c66521951bdfbbffe05aa2a906b352e21058a",
    ),
}

STATE0_SAFE_7B_1E_SHA256 = (
    "93401e0b252146738d78212938ea6646e946c3a4ed9f88535fbeab1eff05baaf"
)


def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | (addr & 0xFFFF)


def hirom_file_from_cpu(bank: int, addr: int) -> int:
    """Map either 80-BF runtime mirror or C0-FF file-bank address to ROM."""
    return ((bank & 0x3F) << 16) | (addr & 0xFFFF)


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

    # Compact A0 nested-call entry.  This body saves the caller VM context,
    # advances/pushes the continuation, replaces $98/$99/$9A with the embedded
    # 24-bit target and increments $1266 before returning to the scheduler.
    # It does not write $1398/$1399 or re-enter C0:C9E7, so a callsite already
    # proven reachable in state0 seeds the nested target in the same mode.
    a0 = file_from_cpu(0xC4, 0x846F)
    expected_a0 = bytes.fromhex(
        "AD 6B 12 48 A5 98 48 A5 99 48 A5 9A 48 A9 04 20 10 84 "
        "20 B9 84 68 85 9A 68 85 99 68 85 98 A0 01 B7 98 48 C8 "
        "B7 98 48 C8 B7 98 85 9A 68 85 99 68 85 98 C8 68 8D 6B "
        "12 EE 66 12 68 68 4C 78 80"
    )
    if rom[a0 : a0 + len(expected_a0)] != expected_a0:
        raise SystemExit("unexpected A0 nested-call handler body at C4:846F")

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

    # Opcode 0x15 consumes two operands, stores the first to $1134 and calls
    # BAB8 with the second.  Its synchronous BAB8 -> AC1E path has no
    # $1398/$1399 write or C0:C9E7 re-entry.  It is only admitted as the
    # *final* instruction before 0x50 because its registered callback can later
    # alter $035F.
    op15 = file_from_cpu(0xC4, 0x8AE0)
    expected15 = bytes.fromhex(
        "B7 98 8D 34 11 C8 B7 98 C8 22 B8 BA 80 4C 0F 84"
    )
    if rom[op15 : op15 + len(expected15)] != expected15:
        raise SystemExit("unexpected opcode 0x15 handler body at C4:8AE0")

    # Upper-range VM grammar. Bytes A0..AF and B0..BF are intercepted by the
    # scheduler before the ordinary opcode dispatcher.
    range_dispatch = file_from_cpu(0xC4, 0x809C)
    expected_range = bytes.fromhex(
        "A0 01 A7 98 C9 E0 90 03 4C 2D 81 "
        "C9 D0 90 03 4C 08 81 C9 C0 90 03 4C 4F 81 "
        "C9 B0 B0 6A C9 A0 90 03 4C 45 81 20 A2 87 80 C7"
    )
    if rom[range_dispatch : range_dispatch + len(expected_range)] != expected_range:
        raise SystemExit("unexpected upper-range VM dispatcher at C4:809B")

    # A3 -> 83E3: bit test -> boolean push.  B2/B3/B4 are relative branches.
    anchors = {
        (0xC4, 0x8184): bytes.fromhex("E3 83"),  # A3 jump-table entry
        (0xC4, 0x818F): bytes.fromhex("23 82"),  # B2
        (0xC4, 0x8191): bytes.fromhex("15 82"),  # B3
        (0xC4, 0x8193): bytes.fromhex("0A 82"),  # B4
        (0xC4, 0x83E3): bytes.fromhex(
            "20 ED 83 3D 46 12 D0 9C 80 9F"
        ),
        (0xC4, 0x820A): bytes.fromhex(
            "20 42 84 86 9E 05 9E D0 10 80 09"
        ),
        (0xC4, 0x8215): bytes.fromhex(
            "20 42 84 86 9E 05 9E F0 05 A9 02 4C 10 84"
        ),
        (0xC4, 0x8223): bytes.fromhex(
            "A2 00 B7 98 10 01 CA 18 65 98 85 98 "
            "8A 65 99 85 99 A9 00 65 9A 85 9A 60"
        ),
        # Normal conditions used by the newly reachable CFG family.
        (0xC4, 0x8A0D): bytes.fromhex(
            "B7 98 85 2A C8 B7 98 85 2B C8 B2 2A "
            "38 F7 98 20 3F 89 A9 04 4C 10 84"
        ),
        (0xC4, 0x9679): bytes.fromhex(
            "AD 06 03 38 F7 98 20 3F 89 4C 5E 89"
        ),
        # C0..CD encode small unsigned literals directly in the low nibble.
        # CE/CF are extended literal forms, but residual state0 uses C2 only.
        (0xC4, 0x814F): bytes.fromhex(
            "29 0F 85 9E 64 9F C9 0E F0 10 C9 0F D0 11 B7 98 85 "
            "9E C8 B7 98 85 9F C8 80 05 B7 98 85 9E C8 20 0F 84 "
            "A5 9E A6 9F 20 24 84 4C 8C 80"
        ),
        # E0..EF scheduler: subtract E0, advance current script by one byte,
        # then jump through the E-handler table at C4:81BD.
        (0xC4, 0x812D): bytes.fromhex(
            "38 E9 E0 0A 48 A9 01 20 10 84 20 42 84 85 A0 86 A1 "
            "FA 20 BA 81 4C 8C 80"
        ),
        # E0/E1/E7/E8 handler entries.
        (0xC4, 0x81BD): bytes.fromhex("BC 82"),
        (0xC4, 0x81BF): bytes.fromhex("51 83"),
        (0xC4, 0x81CB): bytes.fromhex("2F 83"),
        (0xC4, 0x81CD): bytes.fromhex("40 83"),
        # E0 is a no-op over the prepared expression accumulator.
        (0xC4, 0x82BC): bytes.fromhex("60"),
        # E1: boolean zero-test over the expression accumulator.
        (0xC4, 0x8351): bytes.fromhex(
            "A5 A0 05 A1 D0 35 80 2E"
        ),
        # E7: boolean conjunction over the expression accumulator
        # and the previously stacked operand.
        (0xC4, 0x832F): bytes.fromhex(
            "20 9B 83 A5 A0 05 A1 F0 54 A5 9E 05 9F F0 4E 80 47"
        ),
        # E8: expression-stack comparison/boolean operator.
        (0xC4, 0x8340): bytes.fromhex(
            "20 9B 83 A5 A0 05 A1 D0 3E A5 9E 05 9F D0 38 80 3B"
        ),
        # Helpers used by the E comparison family remain inside the expression
        # stack and do not touch map-mode state.
        (0xC4, 0x8391): bytes.fromhex(
            "20 42 84 E4 A1 D0 02 C5 A0 60"
        ),
        (0xC4, 0x839B): bytes.fromhex(
            "20 42 84 85 9E 86 9F 60"
        ),
        # Normal opcode 0x64 consumes one flag byte. The residual
        # state0 family uses 64 00: it clears $0307, skips the optional bit
        # branches, calls 81:98A6, and advances the VM pointer by two bytes.
        (0xC4, 0x92A9): bytes.fromhex(
            "B7 98 8D 07 03 89 02 F0 06 AD 05 03 8D 06 03 AD 07 03 "
            "89 01 F0 04 22 04 82 81 22 A6 98 81 4C 5E 89"
        ),
        (0xC4, 0x895E): bytes.fromhex(
            "A9 02 4C 10 84"
        ),
        (0xC1, 0x98A6): bytes.fromhex(
            "AD 5A 15 8D 59 15 AD 5F 15 0D 0A 03 D0 07 AD 07 03 "
            "89 05 F0 05 A9 01 8D 59 15 6B"
        ),
        # Normal opcode 0x13 writes one operand to $035F and advances
        # by two bytes. The state0 residual family uses 13 02, which preserves
        # the already proven descriptor index 2.
        (0xC4, 0x8A94): bytes.fromhex(
            "B7 98 C8 8D 5F 03 4C 0F 84"
        ),
        # D0..DF scheduler consumes two operand bytes before dispatch.
        (0xC4, 0x8108): bytes.fromhex(
            "48 B7 98 85 9C C8 B7 98 85 9D C8 20 0F 84 A0 01 68 "
            "29 0F 0A AA 20 9B 81 4C 8C 80"
        ),
        (0xC4, 0x819E): bytes.fromhex("4F 82"),
        (0xC4, 0x81A8): bytes.fromhex("6D 82"),
        # D0 reads a 16-bit value through the operand pointer and pushes it.
        (0xC4, 0x824F): bytes.fromhex(
            "B2 9C 4C 1E 84"
        ),
        # D5 pops one expression value and stores it through the operand pointer.
        (0xC4, 0x826D): bytes.fromhex(
            "20 5E 84 92 9C 60"
        ),
        (0xC4, 0x841E): bytes.fromhex(
            "A2 00 20 24 84 60"
        ),
        (0xC4, 0x845E): bytes.fromhex(
            "C2 10 A6 96 BF 8A 71 7E 48 BF 89 71 7E E2 10 FA 60"
        ),
        # Normal opcode 0x3D is variable-length. The residual state0 family
        # uses only subtype 0x02. 935C calls C2CC, whose subtype-2 dispatch
        # entry is C3:A9; both outcomes there return A=2, and 935C increments
        # that to three bytes before advancing the VM pointer.
        (0xC4, 0x935C): bytes.fromhex(
            "9C 57 19 20 14 89 22 CC C2 84 1A 20 10 84 AD 57 19 "
            "20 1E 84 60"
        ),
        (0xC4, 0xC2CC): bytes.fromhex(
            "5A DA A7 0F 0A AA A0 01 20 DA C2 FA 7A 6B"
        ),
        (0xC4, 0xC2E1): bytes.fromhex("A9 C3"),
        (0xC4, 0xC3A9): bytes.fromhex(
            "B7 0F F0 04 C9 0E 90 04 00 EA A9 01 CD 49 18 D0 A8 "
            "4C 53 C3"
        ),
        (0xC4, 0xC353): bytes.fromhex(
            "A9 02 80 02 A9 01 8D 57 19 18 60"
        ),
        (0xC4, 0xC362): bytes.fromhex(
            "A9 02 80 02 A9 01 9C 57 19 18 60"
        ),
        # A0 nested-call / B0 return contract.
        (0xC4, 0x846F): bytes.fromhex(
            "AD 6B 12 48 A5 98 48 A5 99 48 A5 9A 48 A9 04 20 10 84 "
            "20 B9 84"
        ),
        (0xC4, 0x81EA): bytes.fromhex(
            "64 A2 64 A3 68 68 4C C5 80"
        ),
        (0xC4, 0x80C5): bytes.fromhex(
            "CE 66 12 AD 66 12 CD 67 12 F0 05 20 D9 84 80 A3"
        ),
        (0xC4, 0x84D9): bytes.fromhex(
            "20 42 84 85 A6 20 42 84 86 A5 85 A4 20 42 84 85 9A "
            "8E 6E 12 20 42 84 85 98 86 99 60"
        ),
        # Nested A0-target grammar used by the four residual state0 callers.
        (0xC4, 0x8A24): bytes.fromhex(
            "B7 98 85 2A C8 B7 98 85 2B C8 B2 2A 37 98 20 1E 84 "
            "A9 04 4C 10 84"
        ),
        (0xC4, 0x983A): bytes.fromhex(
            "B7 98 8D 74 1D C8 B7 98 8D 69 1D C8 4C 0F 84"
        ),
        (0xC4, 0x9849): bytes.fromhex(
            "B7 98 8D 68 1D 4C 5E 89"
        ),
        (0xC4, 0x8B16): bytes.fromhex(
            "B7 98 C9 FE B0 0D B7 98 99 C9 15 C8 C0 05 90 F6 4C 0F 84"
        ),
        (0xC4, 0x89A5): bytes.fromhex(
            "B7 98 C2 30 29 FF 00 3A 85 00 0A 65 00 AA BD EE 9B 85 2A "
            "BD EF 9B 85 2B E2 30 20 5E 89 22 C7 89 84 60"
        ),
        (0xC4, 0x89C7): bytes.fromhex("DC 2A 00"),
        (0xC4, 0x9ACB): bytes.fromhex(
            "9C 57 19 20 14 89 22 26 D2 83 08 1A 20 10 84 28"
        ),
    }
    for (bank, addr), expected in anchors.items():
        o = file_from_cpu(bank, addr)
        if rom[o : o + len(expected)] != expected:
            raise SystemExit(
                f"unexpected state0 CFG anchor at {bank:02X}:{addr:04X}"
            )

    # The four approved A0 targets are exact pack-record substreams.  Hash the
    # bounded byte ranges instead of embedding their ROM payloads here.
    for (bank, start), (end_bank, end, expected_sha) in STATE0_SAFE_A0_SUBSTREAMS.items():
        begin_off = file_from_cpu(bank, start)
        end_off = file_from_cpu(end_bank, end)
        got_sha = hashlib.sha256(rom[begin_off:end_off]).hexdigest()
        if got_sha != expected_sha:
            raise SystemExit(
                f"unexpected A0 substream at {bank:02X}:{start:04X}: {got_sha}"
            )

    # Opcode 0x02 uses a packed 24-bit routine table at runtime 84:9BEE.
    op02_table = hirom_file_from_cpu(0x84, 0x9BEE)
    for operand, (bank, start, end, expected_sha) in STATE0_SAFE_OP02_TARGETS.items():
        ptr_off = op02_table + 3 * (operand - 1)
        ptr = u24_file(rom, ptr_off)
        expected_ptr = (bank << 16) | start
        if ptr != expected_ptr:
            raise SystemExit(
                f"unexpected opcode02 target for {operand:02X}: {ptr:06X}"
            )
        begin_off = hirom_file_from_cpu(bank, start)
        end_off = hirom_file_from_cpu(bank, end)
        got_sha = hashlib.sha256(rom[begin_off:end_off]).hexdigest()
        if got_sha != expected_sha:
            raise SystemExit(
                f"unexpected opcode02 routine {bank:02X}:{start:04X}: {got_sha}"
            )

    # Concrete 0x7B subtype 0x1E resolves to runtime 83:D705.
    table_7b = hirom_file_from_cpu(0x83, 0xD237)
    target_7b = u16_file(rom, table_7b + 2 * 0x1E)
    if target_7b != 0xD705:
        raise SystemExit(f"unexpected 7B/1E target: 83:{target_7b:04X}")
    begin_7b = hirom_file_from_cpu(0x83, 0xD705)
    end_7b = hirom_file_from_cpu(0x83, 0xD72D)
    if hashlib.sha256(rom[begin_7b:end_7b]).hexdigest() != STATE0_SAFE_7B_1E_SHA256:
        raise SystemExit("unexpected 7B/1E routine body")


def state0_nested_a0_target_safe(
    rom: bytes,
    target_ptr: int,
) -> tuple[bool, bool]:
    """Prove one concrete A0 nested call stays in state0 and can return via B0.

    This parser is deliberately narrower than the main VM.  A target must be
    one of the four SHA-anchored pointer-bounded substreams above.  Every
    reachable branch is explored; any unknown opcode/operand or boundary escape
    fails the proof.
    """
    bank = (target_ptr >> 16) & 0xFF
    addr = target_ptr & 0xFFFF
    spec = STATE0_SAFE_A0_SUBSTREAMS.get((bank, addr))
    if spec is None:
        return False, False

    end_bank, end_addr, _ = spec
    start = file_from_cpu(bank, addr)
    end = file_from_cpu(end_bank, end_addr)
    descriptor_base = file_from_cpu(0xC3, STATE0_DESCRIPTOR_EXPECTED_PTR)
    b910_table = file_from_cpu(0xC0, 0xB91C)

    def signed8(x: int) -> int:
        return x - 0x100 if x & 0x80 else x

    queue = [start]
    seen: set[int] = set()
    found_return = False
    used_branch = False

    while queue:
        p = queue.pop(0)
        if p in seen:
            continue
        seen.add(p)

        if p < start or p >= end:
            return False, used_branch

        op = rom[p]

        # B0 is the proven nested-return path through 81EA -> 80C5 -> 84D9.
        if op == 0xB0:
            found_return = True
            continue

        if op in STATE0_SAFE_BRANCH_OPS:
            if p + 2 > end:
                return False, used_branch
            used_branch = True
            branch = p + signed8(rom[p + 1])
            if op == 0xB2:
                queue.append(branch)
            else:
                queue.append(p + 2)
                queue.append(branch)
            continue

        # A nested normal map selector does not mutate $1398/$1399.
        if op == 0x50:
            if p + 4 > end:
                return False, used_branch
            queue.append(p + 4)
            continue
        if op == 0x51:
            if p + 3 > end:
                return False, used_branch
            queue.append(p + 3)
            continue

        # C0..CD are one-byte small literals.
        if 0xC0 <= op <= 0xCD:
            queue.append(p + 1)
            continue

        # Concrete nested-only normal opcodes.
        if op == 0x0A:
            if p + 4 > end:
                return False, used_branch
            queue.append(p + 4)
            continue
        if op == 0x41:
            if p + 3 > end:
                return False, used_branch
            queue.append(p + 3)
            continue
        if op == 0x42:
            if p + 2 > end:
                return False, used_branch
            queue.append(p + 2)
            continue
        if op == 0x52:
            # The <FE branch copies exactly four operand bytes to $15C9..15CC.
            if p + 5 > end or rom[p + 1] >= 0xFE:
                return False, used_branch
            queue.append(p + 5)
            continue
        if op == 0x02:
            if p + 2 > end:
                return False, used_branch
            operand = rom[p + 1]
            if operand not in STATE0_SAFE_OP02_TARGETS:
                return False, used_branch
            queue.append(p + 2)
            continue
        if op == 0x64:
            if p + 2 > end or rom[p + 1] not in {0x00, 0x24, 0x70}:
                return False, used_branch
            queue.append(p + 2)
            continue
        if op == 0x7B:
            if p + 2 > end or rom[p + 1] != 0x1E:
                return False, used_branch
            queue.append(p + 2)
            continue
        if op == 0x13:
            if p + 2 > end or rom[p + 1] != STATE0_DESCRIPTOR_INDEX:
                return False, used_branch
            queue.append(p + 2)
            continue
        if op in (0xD0, 0xD5):
            if p + 3 > end:
                return False, used_branch
            operand = rom[p + 1] | (rom[p + 2] << 8)
            if (op, operand) not in {
                (0xD0, 0x1984),
                (0xD5, 0x035E),
                (0xD5, 0x0364),
            }:
                return False, used_branch
            queue.append(p + 3)
            continue
        if op == 0x3D:
            if p + 3 > end or rom[p + 1] != 0x02:
                return False, used_branch
            queue.append(p + 3)
            continue

        length = STATE0_PREFIX_SAFE_LENGTHS.get(op)
        if length is None or p + length > end:
            return False, used_branch

        descriptor_id = None
        if op == 0x10:
            descriptor_id = rom[p + 1]
        elif op == 0x33:
            descriptor_id = rom[p + 3]
        elif op == 0x15:
            # Keep the same fail-closed callback rule used by the outer CFG.
            if p + length >= end or rom[p + length] != 0xB0:
                return False, used_branch

        if descriptor_id is not None:
            if descriptor_id == 0:
                return False, used_branch
            descriptor = descriptor_base + (descriptor_id - 1) * 8
            if descriptor + 8 > len(rom):
                return False, used_branch
            x = (rom[descriptor + 7] & 0xF0) >> 3
            if x & 1:
                return False, used_branch
            call_target = u16_file(rom, b910_table + x)
            if call_target not in STATE0_SAFE_B910_TARGETS:
                return False, used_branch

        queue.append(p + length)

    return found_return, used_branch


def state0_prefix_mode_safe(
    rom: bytes,
    record_index: int,
    entry_id: int,
    stream_start: int,
    stream_end: int,
    target: int,
    *,
    require_record0_entry1: bool = True,
) -> tuple[bool, str, bool]:
    """Prove a stream path reaches target while normal state0 remains active.

    By default this is restricted to the independently proven record0/entry1
    startup family.  Callers that separately prove state0 at another substream
    entry may set require_record0_entry1=False and reuse the same fail-closed CFG.

    The proof is deliberately a small CFG, not a linear byte walker.

    Safe normal operations:
      96/10/11/33 plus condition producers 08/2D and bit-test A3.

    Safe control-flow operations:
      B2 = unconditional signed rel8 branch
      B3 = branch on zero, otherwise +2
      B4 = branch on nonzero, otherwise +2

    0x15 remains special: it is accepted only as the final instruction before
    target because its registered callback can later alter $035F.

    For every 10/33 descriptor operation, state0's explicit $035F=2 seed is
    used to resolve C3:0850 and B910 must land on B924/B944.
    """
    if require_record0_entry1 and (record_index != 0 or entry_id != 0x01):
        return False, "", False

    def signed8(x: int) -> int:
        return x - 0x100 if x & 0x80 else x

    descriptor_base = file_from_cpu(0xC3, STATE0_DESCRIPTOR_EXPECTED_PTR)
    b910_table = file_from_cpu(0xC0, 0xB91C)

    queue = [stream_start]
    seen: set[int] = set()
    b910_targets: set[int] = set()
    used_branch = False

    while queue:
        p = queue.pop(0)
        if p in seen:
            continue
        seen.add(p)

        if p == target:
            label = ",".join(f"C0:{x:04X}" for x in sorted(b910_targets))
            return True, label, used_branch

        if p < stream_start or p >= stream_end:
            continue

        op = rom[p]

        # A0 is a nested script call, not a flat four-byte no-op.  The caller
        # continuation is p+4, but it is admitted only when the exact embedded
        # target is one of the SHA-anchored substreams and every reachable path
        # in that substream is mode-safe and can return through B0.
        if op == 0xA0:
            if p + 4 > stream_end:
                continue
            target_ptr = u24_file(rom, p + 1)
            nested_safe, nested_branch = state0_nested_a0_target_safe(
                rom, target_ptr
            )
            if not nested_safe:
                continue
            used_branch = used_branch or nested_branch
            queue.append(p + 4)
            continue

        if op in STATE0_SAFE_BRANCH_OPS:
            if p + 2 > stream_end:
                continue
            used_branch = True
            branch = p + signed8(rom[p + 1])
            if op == 0xB2:
                queue.append(branch)
            else:
                # Runtime condition is unknown; either successor can represent
                # a normal-mode execution. Both branch handlers are mode-safe.
                queue.append(p + 2)
                queue.append(branch)
            continue

        # C0..CD are one-byte small integer literals.  The anchored
        # C-range dispatcher at C4:814F applies the low nibble directly.
        if 0xC0 <= op <= 0xCD:
            length = 1
        # Opcode 0x64 is admitted only for the residual 64 00 form.
        elif op == 0x64:
            if p + 2 > stream_end or rom[p + 1] != 0x00:
                continue
            length = 2
        # Opcode 0x13 writes its one-byte operand to $035F. Admit it
        # only when it preserves the state0 descriptor index proven by 81:98D1.
        elif op == 0x13:
            if p + 2 > stream_end or rom[p + 1] != STATE0_DESCRIPTOR_INDEX:
                continue
            length = 2
        # D-range operations are three bytes: opcode + 16-bit pointer.
        # Only the concrete residual operands proven mode-safe here are
        # admitted. D0 reads $1984; D5 writes $035E. Neither aliases
        # $035F/$1398/$1399 or changes the map-mode dispatcher.
        elif op in (0xD0, 0xD5):
            if p + 3 > stream_end:
                continue
            operand = rom[p + 1] | (rom[p + 2] << 8)
            if (op, operand) not in {(0xD0, 0x1984), (0xD5, 0x035E)}:
                continue
            length = 3
        # Opcode 0x3D is variable length in general. The residual
        # state0 map-entry family uses subtype 0x02 only; static anchors above
        # prove that subtype returns payload length 2 and therefore advances
        # the VM pointer by exactly 3 bytes including the opcode.
        elif op == 0x3D:
            if p + 3 > stream_end or rom[p + 1] != 0x02:
                continue
            length = 3
        else:
            length = STATE0_PREFIX_SAFE_LENGTHS.get(op)
            if length is None or p + length > stream_end:
                continue

        descriptor_id = None
        if op == 0x10:
            descriptor_id = rom[p + 1]
        elif op == 0x33:
            descriptor_id = rom[p + 3]
        elif op == 0x15:
            if p + length != target:
                continue

        if descriptor_id is not None:
            if descriptor_id == 0:
                continue
            descriptor = descriptor_base + (descriptor_id - 1) * 8
            if descriptor + 8 > len(rom):
                continue
            last = rom[descriptor + 7]
            x = (last & 0xF0) >> 3
            if x & 1:
                continue
            table_entry = b910_table + x
            if table_entry + 2 > len(rom):
                continue
            call_target = u16_file(rom, table_entry)
            if call_target not in STATE0_SAFE_B910_TARGETS:
                continue
            b910_targets.add(call_target)

        queue.append(p + length)

    return False, "", used_branch

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


def state0_reachable_a0_substreams(
    rom: bytes,
    records: list[dict],
) -> dict[int, list[dict]]:
    """Find valid substreams entered by A0 from a proven state0 entry1 path.

    This is not a raw A0 byte search.  Each candidate callsite must itself be
    reachable as an instruction boundary through state0_prefix_mode_safe(), and
    its embedded 24-bit target must exactly equal a parsed substream start in the
    same canonical pack.  The result proves state0 at nested-substream entry;
    candidate-local prefix safety is checked separately.
    """
    substreams: dict[int, tuple[int, int, int, int]] = {}
    for record in records:
        header = record.get("header")
        if not header:
            continue
        for entry in header["entries"]:
            substreams[entry["start"]] = (
                record["pack_id"],
                record["record_index"],
                entry["entry_id"],
                entry["end"],
            )

    reachable: dict[int, list[dict]] = {}
    for record in records:
        if record["record_index"] != 0:
            continue
        header = record.get("header")
        if not header:
            continue
        for entry in header["entries"]:
            if entry["entry_id"] != 0x01:
                continue
            stream_start = entry["start"]
            stream_end = entry["end"]
            for p in range(stream_start, max(stream_start, stream_end - 3)):
                if rom[p] != 0xA0 or p + 4 > stream_end:
                    continue
                safe, b910_targets, branch_used = state0_prefix_mode_safe(
                    rom,
                    0,
                    0x01,
                    stream_start,
                    stream_end,
                    p,
                )
                if not safe:
                    continue
                target_ptr = u24_file(rom, p + 1)
                bank = (target_ptr >> 16) & 0xFF
                if bank < 0xC0:
                    continue
                target = file_from_cpu(bank, target_ptr & 0xFFFF)
                target_meta = substreams.get(target)
                if target_meta is None:
                    continue
                target_pack, target_record, target_entry, target_end = target_meta
                if target_pack != record["pack_id"]:
                    continue
                reachable.setdefault(target, []).append(
                    {
                        "caller_pack_id": record["pack_id"],
                        "caller_record_index": 0,
                        "caller_entry_id": 0x01,
                        "callsite": p,
                        "target_record_index": target_record,
                        "target_entry_id": target_entry,
                        "target_end": target_end,
                        "b910_targets": b910_targets,
                        "branch_used": branch_used,
                    }
                )
    return reachable


def candidate_rows(rom: bytes, records: list[dict]) -> tuple[list[dict], list[dict]]:
    primary = []
    all_secondary_shape = []
    state0_nested_seeds = state0_reachable_a0_substreams(rom, records)

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
                (
                    state0_safe,
                    state0_b910_targets,
                    state0_cfg_branch_used,
                ) = state0_prefix_mode_safe(
                    rom,
                    record_index,
                    entry_id,
                    stream_start,
                    stream_end,
                    p,
                )

                nested_seed_callers = state0_nested_seeds.get(stream_start, [])
                nested_state0_safe = False
                nested_b910_targets = ""
                nested_cfg_branch_used = False
                if nested_seed_callers:
                    (
                        nested_state0_safe,
                        nested_b910_targets,
                        nested_cfg_branch_used,
                    ) = state0_prefix_mode_safe(
                        rom,
                        record_index,
                        entry_id,
                        stream_start,
                        stream_end,
                        p,
                        require_record0_entry1=False,
                    )
                nested_seed_labels = ";".join(
                    f"0x{x['caller_pack_id']:02X}@{cpu_from_file(x['callsite'])}"
                    for x in nested_seed_callers
                )

                # Count a proof as a promotion only when earlier independent
                # proofs did not already confirm the row.
                state0_prefix_promoted = (
                    state0_safe
                    and not confirmed_signature
                    and not special_impossible
                )
                state0_nested_promoted = (
                    nested_state0_safe
                    and not confirmed_signature
                    and not special_impossible
                    and not state0_prefix_promoted
                )
                normal_mode_confirmed = (
                    confirmed_signature
                    or special_impossible
                    or state0_prefix_promoted
                    or state0_nested_promoted
                )
                if confirmed_signature and special_impossible:
                    evidence = "confirmed_setup_signature_and_special_parse_impossible"
                elif confirmed_signature:
                    evidence = "confirmed_setup_signature"
                elif special_impossible:
                    evidence = "confirmed_normal_special_parse_impossible"
                elif state0_prefix_promoted:
                    evidence = "confirmed_normal_state0_safe_prefix"
                elif state0_nested_promoted:
                    evidence = "confirmed_normal_state0_a0_nested_entry"
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
                    "state0_cfg_branch_used": state0_cfg_branch_used,
                    "state0_nested_entry_seeded": bool(nested_seed_callers),
                    "state0_nested_seed_count": len(nested_seed_callers),
                    "state0_nested_seed_callers": nested_seed_labels,
                    "state0_nested_mode_safe": nested_state0_safe,
                    "state0_nested_promoted": state0_nested_promoted,
                    "state0_nested_b910_targets": nested_b910_targets,
                    "state0_nested_cfg_branch_used": nested_cfg_branch_used,
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
    state0_cfg_promoted = [
        r for r in state0_prefix_promoted if r["state0_cfg_branch_used"]
    ]
    state0_nested_seeded = [r for r in primary if r["state0_nested_entry_seeded"]]
    state0_nested_safe = [r for r in primary if r["state0_nested_mode_safe"]]
    state0_nested_promoted = [r for r in primary if r["state0_nested_promoted"]]
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
    write_csv(
        args.out_dir / "state0_a0_nested_promotions.csv",
        state0_nested_promoted,
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
            "state0 record0/entry1 family is promoted through a small safe CFG "
            "(96/10/11/33/08/2D/A3, C0..CD literals, E0/E1/E7/E8 expression "
            "ops, B2/B3/B4 branches, concrete-safe 13/3D/D0/D5/64 forms, "
            "terminal-only 0x15, and SHA-bounded A0/B0 nested calls); the "
            "state0 helper seeds $035F=2, and every "
            "descriptor-resolved B910 indirect target is one of the cleared "
            "B924/B944 routines. Later-record substreams may also be promoted "
            "when an instruction-aligned A0 callsite is itself proven reachable "
            "from state0 entry1, targets that exact parsed substream in the same "
            "pack, and the nested substream reaches the candidate through the "
            "same fail-closed CFG. Other rows remain mode-gate unresolved."
        ),
        "corpus": corpus,
        "primary": {
            "strong_shape_total": len(primary),
            "confirmed_setup_signature": len(signature_confirmed),
            "confirmed_special_interpretation_impossible": len(special_impossible),
            "state0_prefix_mode_safe_rows": len(state0_prefix_safe),
            "newly_promoted_state0_safe_prefix": len(state0_prefix_promoted),
            "newly_promoted_state0_cfg_branch_rows": len(state0_cfg_promoted),
            "state0_prefix_b910_targets": sorted(
                {
                    target
                    for r in state0_prefix_promoted
                    for target in r["state0_prefix_b910_targets"].split(",")
                    if target
                }
            ),
            "state0_a0_nested_seeded_rows": len(state0_nested_seeded),
            "state0_a0_nested_mode_safe_rows": len(state0_nested_safe),
            "newly_promoted_state0_a0_nested_rows": len(state0_nested_promoted),
            "state0_a0_nested_promoted_addresses": [
                r["command_addr"] for r in state0_nested_promoted
            ],
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
            "state0_a0_nested_promotions.csv",
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
