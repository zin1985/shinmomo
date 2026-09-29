#!/usr/bin/env python3
"""Render opcode-0x51 secondary map layers from proven primary ROM resources.

The configuration index records immediate secondary configurations as
tNN/lNNN.  Opcode 0x51 selects a secondary tileset/layout without loading a new
graphics/palette setup, so each secondary is rendered from the resource state
already proven for its parent primary configuration.

Outputs remain separate RGBA layers.  BG1/BG2 priority compositing is not
performed here.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

import decode_map_layout as mapdec
import render_normal_map_family_from_setup as normal


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"
DEFAULT_RENDERED = REPO / "data/maps/rendered"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rendered_primary_index(rendered_root: Path):
    index = collections.defaultdict(list)
    for path in rendered_root.rglob("map_*.json"):
        if "secondary_layers" in path.parts:
            continue
        try:
            meta = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if "tileset_id" not in meta or "layout_id" not in meta:
            continue
        index[(int(meta["tileset_id"]), int(meta["layout_id"]))].append(path)
    return index


def resource_signature(resources: dict):
    graphics = []
    for item in resources["graphics_resources"]:
        placement = item.get("placement_source")
        if placement == "proven_transition_zero_fill":
            continue
        graphics.append((
            item.get("operand"),
            placement,
            item.get("vram_word_addr"),
        ))
    zero = tuple(
        (item["start_byte"], item["end_byte_exclusive"])
        for item in resources.get("zero_fill_ranges", [])
    )
    return (
        tuple(graphics),
        resources["palette_resource"]["operand"],
        zero,
        resources.get("state0_descriptor_index", 2),
    )


def collect_jobs(config_path: Path, rendered_root: Path):
    primary_index = rendered_primary_index(rendered_root)
    with config_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    jobs = {}
    missing_parents = []
    for row in rows:
        secondaries = [
            (int(ts), int(layout))
            for ts, layout in re.findall(
                r"t(\d+)/l(\d+)",
                row.get("secondary_configurations", ""),
            )
        ]
        if not secondaries:
            continue

        parent_pair = (
            int(row["primary_tileset_id"]),
            int(row["primary_layout_id"]),
        )
        parent_maps = primary_index.get(parent_pair, [])
        if not parent_maps:
            missing_parents.append((parent_pair, row["config_id"]))
            continue

        for parent_map in parent_maps:
            resources_path = parent_map.parent / "resources.json"
            if not resources_path.exists():
                missing_parents.append((parent_pair, str(resources_path)))
                continue
            resources = json.loads(
                resources_path.read_text(encoding="utf-8-sig")
            )
            if resources.get("kind") != "rom_map_setup_resources":
                continue
            signature = resource_signature(resources)
            for secondary in secondaries:
                key = (secondary, signature)
                job = jobs.setdefault(key, {
                    "secondary": secondary,
                    "resources": resources,
                    "resource_dir": str(
                        parent_map.parent.relative_to(REPO)
                    ),
                    "parents": [],
                })
                job["parents"].append({
                    "primary_tileset_id": parent_pair[0],
                    "primary_layout_id": parent_pair[1],
                    "config_id": row["config_id"],
                    "pack_ids_hex": row["pack_ids_hex"],
                    "command_addresses": row["command_addresses"],
                    "map_json": str(parent_map.relative_to(REPO)),
                })
    if missing_parents:
        raise ValueError(f"missing primary render resources: {missing_parents}")
    return jobs


def reconstruct_from_resources(rom: bytes, resources: dict):
    operands = []
    overrides = []
    for item in resources["graphics_resources"]:
        placement = item.get("placement_source")
        operand = item.get("operand")
        if placement == "proven_transition_zero_fill" or operand is None:
            continue
        if placement == "opcode33_explicit_destination":
            overrides.append((int(operand), int(item["vram_word_addr"])))
        else:
            operands.append(int(operand))

    zero_ranges = [
        (int(item["start_byte"]), int(item["end_byte_exclusive"]))
        for item in resources.get("zero_fill_ranges", [])
    ]
    descriptor_index = int(resources.get("state0_descriptor_index", 2))
    palette_operand = int(resources["palette_resource"]["operand"])

    vram, decoded_resources = normal.reconstruct_vram(
        rom, operands, descriptor_index, overrides
    )
    if zero_ranges:
        vram, decoded_resources = normal.apply_zero_fill_resources(
            vram, decoded_resources, zero_ranges
        )
    palette, palette_meta = normal.palette_from_opcode11(
        rom, palette_operand, descriptor_index
    )
    return {
        "vram": vram,
        "decoded_resources": decoded_resources,
        "palette": palette,
        "palette_meta": palette_meta,
        "graphics_operands": operands,
        "graphics_overrides": overrides,
        "zero_fill_ranges": zero_ranges,
        "palette_operand": palette_operand,
        "descriptor_index": descriptor_index,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--rendered-root", type=Path, default=DEFAULT_RENDERED)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    jobs = collect_jobs(args.config_index, args.rendered_root)

    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True)

    per_secondary = collections.Counter(key[0] for key in jobs)
    variant_sequence = collections.defaultdict(int)
    results = []
    failures = []

    for (secondary, _signature), job in sorted(
        jobs.items(),
        key=lambda item: (
            item[0][0][0],
            item[0][0][1],
            str(item[0][1]),
        ),
    ):
        tileset_id, layout_id = secondary
        try:
            state = reconstruct_from_resources(rom, job["resources"])
            layout = mapdec.parse_layout(rom, layout_id)
            if layout["map_mode_low_nibble"] not in (0, 0x80):
                raise ValueError(
                    f"secondary layout mode "
                    f"{layout['map_mode_low_nibble']} is not normal BG"
                )
            expanded = mapdec.expand_tileset(
                rom, layout["grid"], tileset_id
            )["expanded"]
            validation = normal.validate_layout_resources(
                expanded,
                state["vram"],
                state["decoded_resources"],
                state["palette_meta"],
            )
            image = normal.render_rgba(
                expanded, state["vram"], state["palette"]
            )
        except Exception as exc:
            failures.append({
                "tileset_id": tileset_id,
                "layout_id": layout_id,
                "parent_resource_dir": job["resource_dir"],
                "error": str(exc),
            })
            continue

        variant_sequence[secondary] += 1
        suffix = ""
        if per_secondary[secondary] > 1:
            suffix = (
                f"_pal{state['palette_operand']:02X}"
                f"_v{variant_sequence[secondary]}"
            )
        stem = f"t{tileset_id:02d}_l{layout_id:03d}{suffix}"
        png = args.out_dir / f"{stem}.png"
        image.save(png, optimize=True)

        parent_json_path = REPO / job["parents"][0]["map_json"]
        parent_meta = json.loads(
            parent_json_path.read_text(encoding="utf-8-sig")
        )
        parent_png = parent_json_path.parent / parent_meta["output_png"]
        with Image.open(parent_png) as parent_image:
            parent_size = parent_image.size
        meta = {
            "schema_version": 1,
            "kind": "opcode51_secondary_layer_render",
            "tileset_id": tileset_id,
            "layout_id": layout_id,
            "parent_resource_dir": job["resource_dir"],
            "parents": job["parents"],
            "graphics_operands": state["graphics_operands"],
            "graphics_overrides": [
                {"operand": operand, "vram_word_addr": word_addr}
                for operand, word_addr in state["graphics_overrides"]
            ],
            "zero_fill_ranges": [
                {"start_byte": start, "end_byte_exclusive": end}
                for start, end in state["zero_fill_ranges"]
            ],
            "palette_operand": state["palette_operand"],
            "validation": validation,
            "image_width_px": image.width,
            "image_height_px": image.height,
            "parent_image_width_px": parent_size[0],
            "parent_image_height_px": parent_size[1],
            "same_dimensions_as_parent": image.size == parent_size,
            "output_png": png.name,
            "output_png_sha256": sha256_file(png),
        }
        (args.out_dir / f"{stem}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        results.append(meta)
        print(
            f"rendered secondary t{tileset_id:02d}/l{layout_id:03d}: "
            f"{image.size} palette=0x{state['palette_operand']:02X}"
        )

    index = {
        "schema_version": 1,
        "kind": "opcode51_secondary_layer_index",
        "map_count": len(results),
        "secondary_pair_count": len({
            (item["tileset_id"], item["layout_id"]) for item in results
        }),
        "failed_count": len(failures),
        "same_dimension_render_count": sum(
            1 for item in results if item["same_dimensions_as_parent"]
        ),
        "maps": results,
        "failures": failures,
        "policy": (
            "Secondary layouts are exported as separate RGBA layers. "
            "BG1/BG2 priority compositing is intentionally deferred."
        ),
    }
    (args.out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if failures:
        raise SystemExit(f"{len(failures)} secondary renders failed")
    print(
        f"complete: {len(results)} images, "
        f"{index['secondary_pair_count']} secondary pairs"
    )


if __name__ == "__main__":
    main()
