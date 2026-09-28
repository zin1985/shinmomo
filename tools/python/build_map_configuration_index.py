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
    args = ap.parse_args()

    with args.primary.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows or any(r["normal_mode_confirmed"].lower() != "true" for r in rows):
        raise SystemExit("primary catalog must be non-empty and fully confirmed")

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
        stable = tileset == 7 and layout == 15 and variant == 2
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
                "scene_class_hint": "indoor" if stable else "unknown",
                "display_name": "",
                "known_sample_id": "stable_interior_l1" if stable else "",
                "label_evidence": (
                    "data/maps/samples/stable_interior_rom_binding.json" if stable else ""
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
