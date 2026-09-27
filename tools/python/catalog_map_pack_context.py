#!/usr/bin/env python3
"""Catalog the C4 VM pack-context bridge used by map-selector reachability."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"


def off(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | addr


def file_addr(o: int) -> str:
    return f"{0xC0 + (o >> 16):02X}:{o & 0xFFFF:04X}"


def cpu_addr_from_file(o: int) -> str:
    bank = 0x80 + (o >> 16)
    return f"{bank:02X}:{o & 0xFFFF:04X}"


def expect(rom: bytes, bank: int, addr: int, data: bytes, label: str) -> None:
    o = off(bank, addr)
    got = rom[o:o + len(data)]
    if got != data:
        raise SystemExit(
            f"{label}: expected {data.hex(' ')} at {bank:02X}:{addr:04X}, "
            f"got {got.hex(' ')}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/maps/selectors/map_pack_context_summary.json"),
    )
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM SHA-256: {sha}")

    expect(rom, 0xC4, 0x8508, bytes.fromhex("8D 6A 12 5A 8D 6E 12"), "pack loader")
    expect(rom, 0xC4, 0x8016, bytes.fromhex("DA A6 9B AD 6E 12 9D 59 07 FA 60"), "slot save")
    expect(rom, 0xC4, 0x8070, bytes.fromhex("BD 59 07 8D 6E 12"), "slot restore")
    expect(rom, 0xC4, 0x8086, bytes.fromhex("AD 6E 12 9D 59 07"), "slot resave")
    expect(rom, 0xC4, 0x806A, bytes.fromhex("22 76 80 84"), "child runner entry")
    expect(
        rom, 0xC4, 0x89D6,
        bytes.fromhex("B7 98 8D 6E 12 20 16 80 4C 5E 89"),
        "opcode04 pack switch",
    )

    dt = off(0xC4, 0x87D4)
    handler04 = rom[dt + 2 * 0x04] | (rom[dt + 2 * 0x04 + 1] << 8)
    if handler04 != 0x89D6:
        raise SystemExit(f"opcode 0x04 dispatch mismatch: {handler04:04X}")

    jsl = bytes.fromhex("22 08 85 84")
    callers = []
    pos = 0
    while True:
        k = rom.find(jsl, pos)
        if k < 0:
            break
        callers.append(k)
        pos = k + 1

    expected_callers = {
        off(0xC1, 0x96D1),
        off(0xC1, 0x98DF),
        off(0xC2, 0x912B),
        off(0xC4, 0x871E),
        off(0xC5, 0xCAC5),
    }
    if set(callers) != expected_callers:
        raise SystemExit(
            "unexpected $84:8508 caller set: "
            + ", ".join(file_addr(x) for x in callers)
        )

    caller_rows = []
    for k in callers:
        pre3 = rom[k - 3:k]
        source_kind = "unknown"
        source = ""
        if pre3[0] == 0xAD:
            source_kind = "absolute_wram"
            source = "$%04X" % (pre3[1] | (pre3[2] << 8))
        elif rom[k - 2] == 0xA9:
            source_kind = "immediate"
            source = "0x%02X" % rom[k - 1]
        caller_rows.append(
            {
                "file_mirror_addr": file_addr(k),
                "runtime_cpu_addr": cpu_addr_from_file(k),
                "source_kind": source_kind,
                "source": source,
            }
        )

    expect(rom, 0xC1, 0x96CE, bytes.fromhex("AD 05 03 22 08 85 84"), "state0 pack source")
    expect(rom, 0xC2, 0x9129, bytes.fromhex("A9 19 22 08 85 84"), "state1 pack source")
    expect(rom, 0xC5, 0xCAC3, bytes.fromhex("A9 14 22 08 85 84"), "state5 pack source")
    expect(rom, 0xC3, 0xB7D4, bytes.fromhex("A9 05 8D 99 13"), "state2 to 5")
    expect(rom, 0xC6, 0x8308, bytes.fromhex("9C 99 13 5C E7 C9 80"), "state3 to 0")
    expect(rom, 0xC1, 0xE481, bytes.fromhex("A9 05 8D 99 13 5C E7 C9 80"), "state6 to 5")

    result = {
        "schema_version": 1,
        "kind": "map_pack_context_reachability",
        "rom_sha256": sha,
        "address_note": (
            "file-mirror Cx addresses correspond to runtime CPU 8x addresses "
            "for these code-bank anchors."
        ),
        "pack_context_loader": {
            "file_mirror_entry": "C4:8508",
            "runtime_cpu_entry": "84:8508",
            "historical_correction": (
                "Older notes called the entry C4/84:8509. 8508 is the actual "
                "instruction boundary (STA $126A); 84F5..8507 is a separate helper."
            ),
            "direct_jsl_callers": caller_rows,
        },
        "mode_pack_normalization": [
            {"state": 0, "routine": "81:964E", "pack_source": "$0305", "loader_call": "81:96D1", "classification": "dynamic"},
            {"state": 1, "routine": "82:8F1B", "pack_source": "0x19", "loader_call": "82:912B", "classification": "fixed"},
            {"state": 2, "routine": "83:B7CD", "transition": 5, "classification": "transitions_to_state5"},
            {"state": 3, "routine": "86:82E2", "transition": 0, "classification": "transitions_to_state0"},
            {"state": 5, "routine": "85:CAA3", "pack_source": "0x14", "loader_call": "85:CAC5", "classification": "fixed"},
            {"state": 6, "routine": "81:E331", "transition": 5, "classification": "transitions_to_state5"},
        ],
        "vm_slot_pack_context": {
            "save_current_pack": {
                "runtime_cpu": "84:8016",
                "operation": "$126E -> $0759,X for the current C4 VM slot",
            },
            "restore_current_pack": {
                "runtime_cpu": "84:8070",
                "operation": "$0759,X -> $126E before slot execution",
            },
            "child_inheritance": {
                "runner_entry": "84:8076",
                "resave": "84:8086",
                "operation": (
                    "nested VM execution retains parent $126E and stores it "
                    "into the child/current slot context"
                ),
            },
            "explicit_pack_switch": {
                "opcode": "0x04",
                "handler": "84:89D6",
                "length_bytes": 2,
                "operation": (
                    "operand -> $126E; JSR $8016 writes the new pack id into "
                    "$0759,X"
                ),
            },
        },
        "reachability_consequence": (
            "Mode entry can normalize a pack id, but pack context persists per "
            "C4 VM slot, is inherited by nested VM execution, and can be changed "
            "by normal opcode 0x04. One mode state therefore must not be assigned "
            "to an entire pack without slot/control-flow evidence."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
