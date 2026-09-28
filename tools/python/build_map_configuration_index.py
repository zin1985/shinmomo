#!/usr/bin/env python3
"""Build a configuration-centric index from the confirmed primary map corpus."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def as_int(row: dict, key: str) -> int:
    return int(row[key])


def config_id(tileset: int, layout: int, variant: int) -> str:
    return f"cfg_t{tileset:02d}_l{layout:03d}_v{variant}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--primary",
        type=Path,
        default=Path("data/maps/selectors/primary_map_selector_catalog.csv"),
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/maps/configurations"),
    )
    ap.add_argument(
        "--runtime-identity-dir",
        type=Path,
        default=Path("data/maps/samples"),
    )
    args = ap.parse_args()

    with args.primary.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows or any(r["normal_mode_confirmed"].lower() != "true" for r in rows):
        raise SystemExit("primary catalog must be non-empty and fully confirmed")

    runtime_by_config: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    if args.runtime_identity_dir.exists():
        for path in sorted(args.runtime_identity_dir.glob("*_runtime_identity.json")):
            identity = json.loads(path.read_text(encoding="utf-8-sig"))
            state = identity["map_state"]
            cid = config_id(
                int(state["primary_tileset_139c"]),
                int(state["primary_layout_139e"]),
                int(state["map_variant_139b"]),
            )
            runtime_by_config[cid].append((path, identity))

    groups: dict[tuple[int, int, int], list[dict]] = defaultdict(list)
    for row in rows:
        key = (
            as_int(row, "primary_tileset_id"),
            as_int(row, "primary_layout_id"),
            as_int(row, "map_variant"),
        )
        groups[key].append(row)

    out = []
    secondary_configs: set[tuple[int, int]] = set()
    for (tileset, layout, variant), members in sorted(groups.items()):
        first = members[0]
        packs = sorted({as_int(r, "pack_id_dec") for r in members})
        entries = sorted({as_int(r, "entry_id_dec") for r in members})
        record_refs = sorted(
            {(as_int(r, "pack_id_dec"), as_int(r, "record_index")) for r in members}
        )
        secondary = sorted(
            {
                (as_int(r, "secondary_tileset_id"), as_int(r, "secondary_layout_id"))
                for r in members
                if r["immediate_secondary"].lower() == "true"
            }
        )
        secondary_configs.update(secondary)
        evidence_counts = Counter(r["evidence_class"] for r in members)

        cid = config_id(tileset, layout, variant)
        runtime_records = runtime_by_config.get(cid, [])
        member_by_addr = {r["command_addr"]: r for r in members}
        for path, identity in runtime_records:
            resolved = identity.get("resolved_rom_identity", {})
            if resolved.get("config_id") not in (None, cid):
                raise SystemExit(f"runtime config mismatch in {path}")
            command_addr = resolved.get("command_addr")
            if command_addr and command_addr not in member_by_addr:
                raise SystemExit(
                    f"runtime command {command_addr} is not in {cid}: {path}"
                )
            if command_addr and resolved.get("pack_id_hex") not in (
                None,
                member_by_addr[command_addr]["pack_id_hex"],
            ):
                raise SystemExit(f"runtime pack mismatch in {path}")

        runtime_commands = sorted(
            {
                identity.get("resolved_rom_identity", {}).get("command_addr")
                for _, identity in runtime_records
                if identity.get("resolved_rom_identity", {}).get("command_addr")
            }
        )
        runtime_packs = sorted(
            {
                identity.get("resolved_rom_identity", {}).get("pack_id_hex")
                for _, identity in runtime_records
                if identity.get("resolved_rom_identity", {}).get("pack_id_hex")
            }
        )
        scene_hints = sorted(
            {
                identity.get("scene_observation", {}).get("scene_class")
                for _, identity in runtime_records
                if identity.get("scene_observation", {}).get("scene_class")
            }
        )
        display_names = sorted(
            {
                identity.get("scene_observation", {}).get("exact_in_game_place_name")
                for _, identity in runtime_records
                if identity.get("scene_observation", {}).get("exact_in_game_place_name")
            }
        )
        out.append(
            {
                "config_id": cid,
                "primary_tileset_id": tileset,
                "primary_tileset_ptr": first["primary_tileset_ptr"],
                "primary_layout_id": layout,
                "primary_layout_ptr": first["layout_ptr"],
                "map_variant": variant,
                "layout_flags": first["layout_flags"],
                "layout_width_chunks": as_int(first, "layout_width_chunks"),
                "layout_height_chunks": as_int(first, "layout_height_chunks"),
                "logical_width_metatiles": as_int(first, "logical_width_metatiles"),
                "logical_height_metatiles": as_int(first, "logical_height_metatiles"),
                "occurrence_count": len(members),
                "pack_ids_hex": ";".join(f"0x{x:02X}" for x in packs),
                "record_refs": ";".join(f"0x{p:02X}:r{r}" for p, r in record_refs),
                "entry_ids_hex": ";".join(f"0x{x:02X}" for x in entries),
                "command_addresses": ";".join(r["command_addr"] for r in members),
                "immediate_secondary_occurrences": sum(
                    r["immediate_secondary"].lower() == "true" for r in members
                ),
                "secondary_configurations": ";".join(
                    f"t{st:02d}/l{sl:03d}" for st, sl in secondary
                ),
                "evidence_class_counts": ";".join(
                    f"{k}:{v}" for k, v in sorted(evidence_counts.items())
                ),
                "runtime_bound_sample_count": len(runtime_records),
                "runtime_bound_pack_ids_hex": ";".join(runtime_packs),
                "runtime_bound_command_addresses": ";".join(runtime_commands),
                "runtime_identity_samples": ";".join(
                    identity.get("sample_id", path.stem)
                    for path, identity in runtime_records
                ),
                "runtime_identity_evidence": ";".join(
                    str(path).replace("\\", "/") for path, _ in runtime_records
                ),
                "scene_class_hint": ";".join(scene_hints) if scene_hints else "unknown",
                "display_name": ";".join(display_names),
                "known_sample_id": ";".join(
                    identity.get("sample_id", "") for _, identity in runtime_records
                ),
                "label_evidence": ";".join(
                    str(path).replace("\\", "/") for path, _ in runtime_records
                ),
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "map_configuration_index.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

    counts = Counter(int(r["occurrence_count"]) for r in out)
    summary = {
        "schema_version": 1,
        "kind": "confirmed_map_configuration_index",
        "source": str(args.primary).replace("\\", "/"),
        "primary_occurrence_count": len(rows),
        "configuration_count": len(out),
        "configurations_with_immediate_secondary": sum(
            int(r["immediate_secondary_occurrences"]) > 0 for r in out
        ),
        "distinct_secondary_configurations": len(secondary_configs),
        "occurrence_count_distribution": {
            str(k): v for k, v in sorted(counts.items())
        },
        "max_occurrence_count": max(int(r["occurrence_count"]) for r in out),
        "stable_interior_config_id": config_id(7, 15, 2),
        "runtime_identity_sample_count": sum(
            int(r["runtime_bound_sample_count"]) for r in out
        ),
        "runtime_bound_configuration_count": sum(
            int(r["runtime_bound_sample_count"]) > 0 for r in out
        ),
        "runtime_bound_unique_occurrence_count": len(
            {
                addr
                for r in out
                for addr in r["runtime_bound_command_addresses"].split(";")
                if addr
            }
        ),
        "human_labeled_configuration_count": sum(bool(r["display_name"]) for r in out),
        "scene_class_hint_count": sum(r["scene_class_hint"] != "unknown" for r in out),
        "outputs": ["map_configuration_index.csv", "map_configuration_summary.json"],
    }
    (args.out_dir / "map_configuration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
