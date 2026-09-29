#!/usr/bin/env python3
"""Build a consolidated catalog of recovered Shinmomo map render artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_RENDERED = REPO / "data/maps/rendered"
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"

NON_IMMEDIATE_REFERENCES = {
    (42, 164): {
        "artifact_role": "secondary_layer_non_immediate",
        "evidence": "pack 0x9D normal-mode path CC:FB98: 51 2A A4",
    },
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def primary_config_index(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_pair = {}
    secondary_pairs = set()
    for row in rows:
        pair = (int(row["primary_tileset_id"]), int(row["primary_layout_id"]))
        by_pair.setdefault(pair, []).append({
            "config_id": row["config_id"],
            "variant": int(row["map_variant"]),
            "pack_ids_hex": row.get("pack_ids_hex", ""),
            "command_addresses": row.get("command_addresses", ""),
            "display_name": row.get("display_name", ""),
            "label_status": row.get("label_status", ""),
        })
        for ts, layout in re.findall(
            r"t(\d+)/l(\d+)", row.get("secondary_configurations", "")
        ):
            secondary_pairs.add((int(ts), int(layout)))
    return rows, by_pair, secondary_pairs


def classify_primary_dir(name: str):
    if name == "world_mode7_tileset_01" or name.startswith("mode7_tileset_"):
        return "mode7_primary"
    if name == "tileset_04":
        return "normal_primary"
    if name.startswith("dungeon_tileset_"):
        return "normal_primary"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rendered-root", type=Path, default=DEFAULT_RENDERED)
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    config_rows, configs_by_pair, secondary_pairs = primary_config_index(
        args.config_index
    )
    records = []

    # Primary / Mode7 render directories.
    for directory in sorted(args.rendered_root.iterdir()):
        if not directory.is_dir():
            continue
        role = classify_primary_dir(directory.name)
        if role is None:
            continue
        for meta_path in sorted(directory.glob("map_*.json")):
            try:
                meta = read_json(meta_path)
            except Exception:
                continue
            if "tileset_id" not in meta or "layout_id" not in meta:
                continue
            ts = int(meta["tileset_id"])
            layout = int(meta["layout_id"])
            png = directory / meta.get(
                "output_png", f"map_{layout:03d}.png"
            )
            config_entries = configs_by_pair.get((ts, layout), [])
            special_ref = NON_IMMEDIATE_REFERENCES.get((ts, layout))
            actual_role = (
                special_ref["artifact_role"] if special_ref else role
            )
            records.append({
                "artifact_role": actual_role,
                "tileset_id": ts,
                "layout_id": layout,
                "config_ids": ";".join(x["config_id"] for x in config_entries),
                "variants": ";".join(
                    str(x["variant"]) for x in config_entries
                ),
                "display_names": ";".join(
                    x["display_name"] for x in config_entries
                    if x["display_name"]
                ),
                "label_statuses": ";".join(
                    x["label_status"] for x in config_entries
                    if x["label_status"]
                ),
                "parent_config_id": "",
                "primary_tileset_id": "",
                "primary_layout_id": "",
                "secondary_tileset_id": "",
                "secondary_layout_id": "",
                "bg_assignment": "",
                "palette_operand": meta.get("palette_operand", ""),
                "image_width_px": meta.get("image_width_px", ""),
                "image_height_px": meta.get("image_height_px", ""),
                "png": rel(png) if png.exists() else "",
                "json": rel(meta_path),
                "confidence": (
                    "canonical_referenced_non_immediate"
                    if special_ref
                    else "canonical_referenced"
                ),
                "notes": (
                    special_ref["evidence"]
                    if special_ref
                    else meta.get("render_mode", "")
                ),
            })

    # Opcode-0x51 secondary layers.
    secondary_dir = args.rendered_root / "secondary_layers"
    secondary_index = read_json(secondary_dir / "index.json")
    for meta in secondary_index["maps"]:
        json_path = secondary_dir / (
            Path(meta["output_png"]).stem + ".json"
        )
        parent_cfgs = sorted({
            p["config_id"] for p in meta.get("parents", [])
        })
        primary_pairs = sorted({
            (p["primary_tileset_id"], p["primary_layout_id"])
            for p in meta.get("parents", [])
        })
        records.append({
            "artifact_role": "secondary_layer",
            "tileset_id": int(meta["tileset_id"]),
            "layout_id": int(meta["layout_id"]),
            "config_ids": ";".join(parent_cfgs),
            "variants": "",
            "display_names": "",
            "label_statuses": "",
            "parent_config_id": ";".join(parent_cfgs),
            "primary_tileset_id": ";".join(str(x[0]) for x in primary_pairs),
            "primary_layout_id": ";".join(str(x[1]) for x in primary_pairs),
            "secondary_tileset_id": int(meta["tileset_id"]),
            "secondary_layout_id": int(meta["layout_id"]),
            "bg_assignment": "",
            "palette_operand": meta.get("palette_operand", ""),
            "image_width_px": meta.get("image_width_px", ""),
            "image_height_px": meta.get("image_height_px", ""),
            "png": rel(secondary_dir / meta["output_png"]),
            "json": rel(json_path),
            "confidence": "canonical_referenced",
            "notes": "opcode_0x51_secondary_layer",
        })

    # Mode-1 BG1/BG2 composites.
    composite_dir = args.rendered_root / "bg12_composites"
    composite_index = read_json(composite_dir / "index.json")
    for meta in composite_index["composites"]:
        json_path = composite_dir / (
            Path(meta["output_png"]).stem + ".json"
        )
        records.append({
            "artifact_role": "bg12_composite",
            "tileset_id": int(meta["primary"]["tileset_id"]),
            "layout_id": int(meta["primary"]["layout_id"]),
            "config_ids": meta["config_id"],
            "variants": str(meta["variant"]),
            "display_names": "",
            "label_statuses": "",
            "parent_config_id": meta["config_id"],
            "primary_tileset_id": int(meta["primary"]["tileset_id"]),
            "primary_layout_id": int(meta["primary"]["layout_id"]),
            "secondary_tileset_id": int(meta["secondary"]["tileset_id"]),
            "secondary_layout_id": int(meta["secondary"]["layout_id"]),
            "bg_assignment": (
                f"primary=BG{meta['primary']['bg']};"
                f"secondary=BG{meta['secondary']['bg']}"
            ),
            "palette_operand": meta["secondary"].get(
                "palette_operand", ""
            ),
            "image_width_px": meta.get("image_width_px", ""),
            "image_height_px": meta.get("image_height_px", ""),
            "png": rel(composite_dir / meta["output_png"]),
            "json": rel(json_path),
            "confidence": "canonical_referenced",
            "notes": meta.get("layer_alignment", ""),
        })

    # Unreferenced layout probes.
    probe_dir = args.rendered_root / "unreferenced_layout_probes"
    probe_index = read_json(probe_dir / "index.json")
    for probe in probe_index["probes"]:
        meta_path = REPO / probe["json"]
        meta = read_json(meta_path)
        png = REPO / probe["png"]
        records.append({
            "artifact_role": "unreferenced_probe",
            "tileset_id": int(probe["tileset_id_candidate"]),
            "layout_id": int(probe["layout_id"]),
            "config_ids": "",
            "variants": "",
            "display_names": "",
            "label_statuses": "",
            "parent_config_id": "",
            "primary_tileset_id": "",
            "primary_layout_id": "",
            "secondary_tileset_id": "",
            "secondary_layout_id": "",
            "bg_assignment": "",
            "palette_operand": meta.get("palette_operand", ""),
            "image_width_px": meta.get("image_width_px", ""),
            "image_height_px": meta.get("image_height_px", ""),
            "png": rel(png),
            "json": rel(meta_path),
            "confidence": probe["confidence"],
            "notes": probe["reason"],
        })

    records.sort(key=lambda x: (
        x["artifact_role"],
        int(x["tileset_id"]),
        int(x["layout_id"]),
        x["png"],
    ))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "map_render_catalog.csv"
    fields = list(records[0].keys())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    primary_pairs = {
        (int(r["primary_tileset_id"]), int(r["primary_layout_id"]))
        for r in config_rows
    }
    referenced_layout_ids = {
        int(r["primary_layout_id"]) for r in config_rows
    } | {layout for _, layout in secondary_pairs} | {
        layout for _, layout in NON_IMMEDIATE_REFERENCES
    }
    all_layout_ids = set(range(1, 204))
    unreferenced_layout_ids = sorted(all_layout_ids - referenced_layout_ids)

    role_counts = {}
    for record in records:
        role_counts[record["artifact_role"]] = (
            role_counts.get(record["artifact_role"], 0) + 1
        )

    summary = {
        "schema_version": 1,
        "kind": "map_render_master_catalog",
        "artifact_count": len(records),
        "role_counts": role_counts,
        "primary_configuration_count": len(config_rows),
        "primary_pair_count": len(primary_pairs),
        "secondary_pair_count": len(secondary_pairs),
        "bg12_composite_count": composite_index["composite_count"],
        "bg12_skipped_count": composite_index["skipped_count"],
        "unreferenced_layout_ids": unreferenced_layout_ids,
        "unreferenced_probe_count": probe_index["probe_count"],
        "unrendered_unreferenced_layout_ids": sorted(
            set(unreferenced_layout_ids)
            - {int(x["layout_id"]) for x in probe_index["probes"]}
        ),
        "rendered_layout_ids": sorted({int(x["layout_id"]) for x in records}),
        "unrendered_layout_ids_1_203": sorted(
            set(range(1, 204))
            - {int(x["layout_id"]) for x in records}
        ),
        "records": records,
    }
    (args.out_dir / "map_render_catalog.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("artifacts", len(records))
    print("roles", role_counts)
    print("primary_pairs", len(primary_pairs))
    print("secondary_pairs", len(secondary_pairs))
    print("bg12_composites", composite_index["composite_count"])
    print("unreferenced_layouts", unreferenced_layout_ids)
    print(
        "unrendered_unreferenced",
        summary["unrendered_unreferenced_layout_ids"],
    )
    print("unrendered_layout_ids_1_203", summary["unrendered_layout_ids_1_203"])


if __name__ == "__main__":
    main()
