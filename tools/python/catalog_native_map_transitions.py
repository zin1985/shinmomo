#!/usr/bin/env python3
"""Catalog native (non-C4-VM 0x53/0x56) map-state transition candidates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import catalog_map_selectors as cms

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

CANDIDATE_COLUMNS = [
    "trigger_type", "trigger_addr", "trigger_variant", "condition",
    "source_pack", "source_config_id",
    "destination_pack", "destination_config_id", "destination_layout",
    "destination_tileset", "destination_variant",
    "destination_x", "destination_y", "destination_entrance",
    "confidence", "evidence", "provenance",
]

WRITER_COLUMNS = [
    "writer_addr", "routine", "classification", "transition_candidate",
    "pack_value", "write_source", "state_effect", "confidence", "evidence",
]


def hx(v: int) -> str:
    return f"0x{v:02X}"


def cpu(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def rom_off(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | (addr & 0xFFFF)


def rb(rom: bytes, bank: int, addr: int) -> int:
    return rom[rom_off(bank, addr)]


def rw(rom: bytes, bank: int, addr: int) -> int:
    return rb(rom, bank, addr) | (rb(rom, bank, addr + 1) << 8)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def load_pack_configs(root: Path) -> dict[int, dict]:
    selectors = read_csv(root / "data/maps/selectors/primary_map_selector_catalog.csv")
    configs = read_csv(root / "data/maps/configurations/map_configuration_index.csv")
    config_by_tuple = {
        (
            int(r["primary_tileset_id"]),
            int(r["primary_layout_id"]),
            int(r["map_variant"]),
        ): r
        for r in configs
    }
    ids_by_pack: dict[int, set[str]] = defaultdict(set)
    by_id = {r["config_id"]: r for r in configs}
    for row in selectors:
        if (
            int(row["record_index"]) == 0
            and int(row["entry_id_dec"]) == 1
            and row["normal_mode_confirmed"].lower() == "true"
        ):
            key = (
                int(row["primary_tileset_id"]),
                int(row["primary_layout_id"]),
                int(row["map_variant"]),
            )
            cfg = config_by_tuple.get(key)
            if cfg:
                ids_by_pack[int(row["pack_id_dec"])].add(cfg["config_id"])
    out = {}
    for pack_id, ids in ids_by_pack.items():
        if len(ids) == 1:
            out[pack_id] = by_id[next(iter(ids))]
    return out


def candidate_row(pack_configs: dict[int, dict], **values) -> dict:
    row = {key: "" for key in CANDIDATE_COLUMNS}
    row.update(values)
    pack_text = row["destination_pack"]
    if pack_text:
        pack_id = int(pack_text, 16)
        cfg = pack_configs.get(pack_id)
        if cfg:
            row["destination_config_id"] = cfg["config_id"]
            row["destination_layout"] = cfg["primary_layout_id"]
            row["destination_tileset"] = cfg["primary_tileset_id"]
            row["destination_variant"] = cfg["map_variant"]
    return row


def writer_rows() -> list[dict]:
    return [
        {
            "writer_addr": "C1:8255", "routine": "C1:8244",
            "classification": "saved_map_state_restore",
            "transition_candidate": "false", "pack_value": "",
            "write_source": "$1521,X -> $0305",
            "state_effect": "restores saved pack/x/y/secondary-x/secondary-y/entrance",
            "confidence": "confirmed",
            "evidence": "indexed state fields $151D..$1522 are copied back to active map state",
        },
        {
            "writer_addr": "C1:99ED", "routine": "C1:99CF",
            "classification": "slot0_restore_and_reseed",
            "transition_candidate": "false", "pack_value": "",
            "write_source": "$1521 -> $0305",
            "state_effect": "restores slot0 map state, then reinitializes/saves state stack",
            "confidence": "confirmed",
            "evidence": "copies $151D/$151E/$1522/$1521 to active fields then calls 81:8204/81:8207",
        },
        {
            "writer_addr": "C1:EE43", "routine": "C1:EE3C",
            "classification": "temporary_pack_context_override",
            "transition_candidate": "false", "pack_value": "0x83",
            "write_source": "literal 0x83 -> $0305",
            "state_effect": "temporarily overrides pack while original $0305 is on CPU stack",
            "confidence": "confirmed",
            "evidence": "C1:EE3C saves $0305 with PHA; C1:EE73 restores it before RTL",
        },
        {
            "writer_addr": "C1:EE73", "routine": "C1:EE3C",
            "classification": "temporary_pack_context_restore",
            "transition_candidate": "false", "pack_value": "",
            "write_source": "PLA -> $0305",
            "state_effect": "restores the temporary override from C1:EE43",
            "confidence": "confirmed",
            "evidence": "paired stack save/restore in one routine",
        },
        {
            "writer_addr": "C5:9240", "routine": "C5:921C",
            "classification": "temporary_pack_context_restore",
            "transition_candidate": "false", "pack_value": "",
            "write_source": "PLA -> $0305",
            "state_effect": "restores pack after temporary native operation",
            "confidence": "confirmed",
            "evidence": "C5:9222 pushes $0305; C5:9240 restores it before RTS",
        },
        {
            "writer_addr": "C5:9310", "routine": "C5:92F2",
            "classification": "native_literal_destination_table",
            "transition_candidate": "true", "pack_value": "0x4C",
            "write_source": "literal 0x4C -> $0305",
            "state_effect": "sets destination x/y from C5:9323 table then signals 81:837F",
            "confidence": "strong_candidate",
            "evidence": "literal pack write plus table-driven $1573/$157D and JSL 81:837F",
        },
        {
            "writer_addr": "C5:CB81", "routine": "C5:CB7C",
            "classification": "native_literal_pack_switch",
            "transition_candidate": "true", "pack_value": "0xF1",
            "write_source": "literal 0xF1 -> $0305",
            "state_effect": "sets entrance from (($195B & 3) * 2) + 2 and clears pending mode",
            "confidence": "structural_candidate",
            "evidence": "literal current-pack write with entrance update; transition finalizer not local",
        },
        {
            "writer_addr": "C6:8027", "routine": "C6:8000",
            "classification": "native_route_stack_builder",
            "transition_candidate": "true", "pack_value": "table",
            "write_source": "C6:8060 pointer-selected route -> $0305",
            "state_effect": "builds saved map-state route via 81:8207; leaves final node active",
            "confidence": "strong_candidate",
            "evidence": "16 pointer-selected route lists decoded as context + repeated pack/x/y/entrance + 00",
        },
        {
            "writer_addr": "C6:8191", "routine": "C6:8164",
            "classification": "native_keyed_route_stack_node",
            "transition_candidate": "true", "pack_value": "table",
            "write_source": "C6:81C9 keyed route node -> $0305",
            "state_effect": "writes intermediate pack/x/y/entrance then saves node via 81:8207",
            "confidence": "confirmed",
            "evidence": "reader searches key table by $0306 and walks 4-byte route nodes",
        },
        {
            "writer_addr": "C6:81B9", "routine": "C6:8164",
            "classification": "native_keyed_route_final",
            "transition_candidate": "true", "pack_value": "table",
            "write_source": "post-terminator final pack -> $0305",
            "state_effect": "leaves final destination pack and entrance active after route-stack build",
            "confidence": "strong_candidate",
            "evidence": "after zero route terminator, reader loads final pack and entrance and returns",
        },
        {
            "writer_addr": "C6:82FD", "routine": "C6:82DD",
            "classification": "native_literal_pack_switch",
            "transition_candidate": "true", "pack_value": "0xED",
            "write_source": "literal 0xED -> $0305",
            "state_effect": "sets entrance 0x02, clears pending mode, then JML 80:C9E7",
            "confidence": "strong_candidate",
            "evidence": "literal current-pack/entrance setup followed by engine tail jump",
        },
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--candidates",
        type=Path,
        default=Path("data/maps/transitions/native_map_transition_candidates.csv"),
    )
    ap.add_argument(
        "--writers",
        type=Path,
        default=Path("data/maps/transitions/native_0305_writer_catalog.csv"),
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=Path("data/maps/transitions/native_map_transition_summary.json"),
    )
    ap.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analysis/native_map_transition_catalog.md"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")
    pack_configs = load_pack_configs(root)
    candidates: list[dict] = []

    # C5:92F2: eight table-selected arrival coordinates, fixed pack 0x4C.
    for selector in range(0, 0x10, 2):
        x = rb(rom, 0xC5, 0x9323 + selector)
        y = rb(rom, 0xC5, 0x9324 + selector)
        candidates.append(candidate_row(
            pack_configs,
            trigger_type="native_literal_pack_table",
            trigger_addr="C5:9310",
            trigger_variant=f"selector=0x{selector:02X}",
            condition="C5:92F2 success path; selector=(80:BB68 & 0x0E)",
            destination_pack="0x4C",
            destination_x=x,
            destination_y=y,
            confidence="strong_candidate",
            evidence=(
                "C5:92F2 writes table-selected $1573/$157D, literal 0x4C to $0305, "
                "then JSL 81:837F"
            ),
            provenance="C5:92F2;C5:9310;C5:9323",
        ))

    candidates.append(candidate_row(
        pack_configs,
        trigger_type="native_literal_pack_switch",
        trigger_addr="C5:CB81",
        trigger_variant="entrance_cycle",
        condition="destination entrance=(($195B & 3) * 2) + 2",
        destination_pack="0xF1",
        confidence="structural_candidate",
        evidence=(
            "C5:CB7C increments $0309, writes literal 0xF1 to $0305, derives "
            "$13B9/$13B8 from $195B, increments $195B, and clears $1399"
        ),
        provenance="C5:CB7C;C5:CB81",
    ))

    # C6:8000: pointer-selected route stack. The final node remains active.
    for index in range(16):
        ptr = rw(rom, 0xC6, 0x8060 + index * 2)
        q = ptr
        context_0306 = rb(rom, 0xC6, q)
        q += 1
        nodes = []
        while True:
            pack = rb(rom, 0xC6, q)
            q += 1
            if pack == 0:
                break
            x = rb(rom, 0xC6, q)
            y = rb(rom, 0xC6, q + 1)
            entrance = rb(rom, 0xC6, q + 2)
            q += 3
            nodes.append((pack, x, y, entrance))
        pack, x, y, entrance = nodes[-1]
        candidates.append(candidate_row(
            pack_configs,
            trigger_type="native_route_stack_final",
            trigger_addr="C6:8027",
            trigger_variant=f"index={index}",
            condition=f"route_ptr=C6:{ptr:04X}; context_0306={hx(context_0306)}",
            destination_pack=hx(pack),
            destination_x=x,
            destination_y=y,
            destination_entrance=hx(entrance),
            confidence="strong_candidate",
            evidence=(
                "C6:8000 clears map-state stack via 81:8204, walks repeated "
                "pack/x/y/entrance nodes, saves non-final nodes via 81:8207, "
                "and leaves the final node in active map state"
            ),
            provenance=f"C6:8000;C6:8027;C6:8060;route=C6:{ptr:04X}",
        ))

    # C6:8164: keyed by $0306. Route nodes are saved, then final pack/entrance remain active.
    q = 0x81C9
    while True:
        key = rb(rom, 0xC6, q)
        if key == 0:
            break
        ptr = rw(rom, 0xC6, q + 1)
        q += 3
        p = ptr
        node_count = 0
        while rb(rom, 0xC6, p) != 0:
            p += 4
            node_count += 1
        final_pack = rb(rom, 0xC6, p + 1)
        final_entrance = rb(rom, 0xC6, p + 2)
        candidates.append(candidate_row(
            pack_configs,
            trigger_type="native_keyed_route_final",
            trigger_addr="C6:81B9",
            trigger_variant=f"key0306={hx(key)}",
            condition=f"route_ptr=C6:{ptr:04X}; saved_nodes={node_count}",
            destination_pack=hx(final_pack),
            destination_entrance=hx(final_entrance),
            confidence="strong_candidate",
            evidence=(
                "C6:8164 matches $0306 against C6:81C9, saves zero or more "
                "pack/x/y/entrance nodes via 81:8207, then after the zero terminator "
                "writes final pack to $0305 and entrance to $13B9/$13B8"
            ),
            provenance=f"C6:8164;C6:8191;C6:81B9;route=C6:{ptr:04X}",
        ))

    candidates.append(candidate_row(
        pack_configs,
        trigger_type="native_literal_pack_switch",
        trigger_addr="C6:82FD",
        trigger_variant="literal_0xED",
        condition="literal path",
        destination_pack="0xED",
        destination_entrance="0x02",
        confidence="strong_candidate",
        evidence=(
            "C6:82FD writes literal 0xED to $0305, entrance 0x02 to "
            "$13B9/$13B8, clears $1399, then JML 80:C9E7"
        ),
        provenance="C6:82DD;C6:82FD",
    ))


    writers = writer_rows()
    args.candidates.parent.mkdir(parents=True, exist_ok=True)
    with args.candidates.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANDIDATE_COLUMNS)
        w.writeheader()
        w.writerows(candidates)
    with args.writers.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=WRITER_COLUMNS)
        w.writeheader()
        w.writerows(writers)

    confidence_counts = Counter(r["confidence"] for r in candidates)
    type_counts = Counter(r["trigger_type"] for r in candidates)
    summary = {
        "schema_version": 1,
        "kind": "native_map_transition_candidate_catalog",
        "generated_against_git_head": git_head(root),
        "rom_sha256": sha,
        "writer_site_count": len(writers),
        "writer_transition_candidate_site_count": sum(
            r["transition_candidate"] == "true" for r in writers
        ),
        "writer_excluded_restore_or_context_site_count": sum(
            r["transition_candidate"] == "false" for r in writers
        ),
        "candidate_count": len(candidates),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "trigger_type_counts": dict(sorted(type_counts.items())),
        "destination_config_resolved_count": sum(
            bool(r["destination_config_id"]) for r in candidates
        ),
        "destination_coordinate_resolved_count": sum(
            r["destination_x"] != "" and r["destination_y"] != ""
            for r in candidates
        ),
        "unique_destination_pack_count": len({
            r["destination_pack"] for r in candidates if r["destination_pack"]
        }),
    }

    summary["structural_findings"] = {
        "state_stack_clear": "81:8204 sets $DD=0",
        "state_stack_save": (
            "81:8207 stores $0305/$1573/$157D/$15C3/$15C4/$13B9 "
            "to indexed $151D..$1522 state slots and advances $DD by 6"
        ),
        "state_stack_restore": (
            "C1:8244 restores indexed saved map state from $151D..$1522"
        ),
        "c6_8000_route_format": (
            "context_0306:1, then repeated [pack,x,y,entrance]:4, then 00"
        ),
        "c6_8164_route_format": (
            "key0306 + ptr16 table; route contains repeated [pack,x,y,entrance], "
            "00 terminator, final_pack, final_entrance"
        ),
    }
    summary["unresolved"] = [
        "native routine callers/triggers are not yet semantically named",
        "source map/config remains null because caller-time $0305 is not statically proven",
        "C5:CB81 has no local transition-finalizer call and stays structural_candidate",
        "native route stack entries are state-stack construction; only the final active destination is promoted",
    ]
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


    doc = """# Native map transition catalog

Updated: 2026-09-29

## Scope

This pass inventories exact native STA $0305 sites outside the already
cataloged C4 VM opcode 0x53/0x56 transition grammar. No HTML viewer or NPC/sprite
integration is included.

Canonical ROM SHA-256: {sha}
Git HEAD used for generation: {head}

## Writer classification

There are **{writer_sites}** exact native STA $0305 sites outside C4:8B7B.
Five are confirmed restore/temporary-context writes and are excluded from
transition candidates. Six belong to routines that construct or leave a
destination map state.

The key correction in this pass is 81:8207: it is a map-state **save** routine,
not a renderer. It copies active $0305/$1573/$157D/$15C3/$15C4/$13B9 into
indexed $151D..$1522 slots and advances $DD by six. 81:8204 clears that stack
and C1:8244 restores an indexed saved state.
""".format(
        sha=sha,
        head=summary["generated_against_git_head"],
        writer_sites=summary["writer_site_count"],
    )

    doc += """
## Candidate families

C5:92F2 / writer C5:9310 selects one of eight X/Y pairs from C5:9323, writes
literal pack 0x4C to $0305, then calls the same 81:837F transition-state helper
used by VM opcode 0x56.

C6:8000 uses a 16-entry pointer table at C6:8060. Each selected route is:
context_0306, repeated [pack,x,y,entrance], then 00. Non-final nodes are saved
with 81:8207; the final node remains in active map state. Only that final node
is promoted into the candidate CSV.

C6:8164 searches the key/pointer table at C6:81C9 using $0306. Each route stores
zero or more [pack,x,y,entrance] states via 81:8207, then after a zero terminator
leaves final_pack and final_entrance active at C6:81B9.

C5:CB7C writes pack 0xF1 with an entrance derived from $195B but has no local
finalizer, so it remains structural_candidate. C6:82DD writes pack 0xED,
entrance 0x02, clears $1399, and jumps to 80:C9E7.
"""

    doc += """
## Counts

- native writer sites: {writer_sites}
- writer sites producing candidate families: {candidate_writer_sites}
- restore/temporary-context writer sites excluded: {excluded_writer_sites}
- native transition candidate rows: {candidate_count}
- strong candidates: {strong}
- structural candidates: {structural}
- rows with unique destination configuration: {configs}
- rows with destination X/Y: {coords}
- distinct destination packs: {packs}

## Conservative policy

source_pack/source_config_id remain blank. These native routines prove the
destination state they construct, but not the caller-time current map. The C6
route-stack intermediates are preserved as route evidence, not promoted as
visible map-to-map edges. Only the final active destination state is cataloged.

## Outputs

- data/maps/transitions/native_map_transition_candidates.csv
- data/maps/transitions/native_0305_writer_catalog.csv
- data/maps/transitions/native_map_transition_summary.json
- docs/analysis/native_map_transition_catalog.md
- tools/python/catalog_native_map_transitions.py

## Remaining blockers
""".format(
        writer_sites=summary["writer_site_count"],
        candidate_writer_sites=summary["writer_transition_candidate_site_count"],
        excluded_writer_sites=summary["writer_excluded_restore_or_context_site_count"],
        candidate_count=summary["candidate_count"],
        strong=confidence_counts.get("strong_candidate", 0),
        structural=confidence_counts.get("structural_candidate", 0),
        configs=summary["destination_config_resolved_count"],
        coords=summary["destination_coordinate_resolved_count"],
        packs=summary["unique_destination_pack_count"],
    )
    for item in summary["unresolved"]:
        doc += "- " + item + "\n"
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(doc, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
