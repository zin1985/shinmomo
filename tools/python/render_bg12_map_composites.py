#!/usr/bin/env python3
"""Compose proven primary + opcode-0x51 secondary layers as SNES Mode-1 BG1/BG2.

This is a background-map composite, not a full screenshot renderer:
sprites and BG3 are intentionally excluded.

Evidence used by this tool:
- normal map initialization selects BGMODE 1 via 80:CB60/CBCD -> 80:A065;
- primary setup 80:CD85 passes map variant V to 80:C6FD;
- secondary setup 80:CDD1 passes 3-V to 80:C6FD;
- 80:C6FD maps 1/2 directly to BG1SC/BG2SC mirrors at $1142/$1144;
- SNES tilemap bit 13 is the priority bit;
- Mode-1 BG1/BG2 relative order is:
  BG1 high > BG2 high > BG1 low > BG2 low.

Only same-dimension primary/secondary configurations are composed.  Mismatched
dimensions are retained as separate layers until their runtime wrap/alignment is
proven.
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

import numpy as np
from PIL import Image

import decode_map_layout as mapdec


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "data/maps/configurations/map_configuration_index.csv"
DEFAULT_RENDERED = REPO / "data/maps/rendered"
DEFAULT_SECONDARY = DEFAULT_RENDERED / "secondary_layers"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def priority_mask(rom: bytes, tileset_id: int, layout_id: int) -> np.ndarray:
    layout = mapdec.parse_layout(rom, layout_id)
    expanded = mapdec.expand_tileset(
        rom, layout["grid"], tileset_id
    )["expanded"]
    entries = np.asarray(expanded, dtype=np.uint16)
    tile_priority = ((entries & 0x2000) != 0).astype(np.uint8)
    return np.repeat(np.repeat(tile_priority, 8, axis=0), 8, axis=1)


def bg_rank(bg: int, priority: np.ndarray) -> np.ndarray:
    if bg == 1:
        return np.where(priority != 0, 4, 2).astype(np.uint8)
    if bg == 2:
        return np.where(priority != 0, 3, 1).astype(np.uint8)
    raise ValueError(f"unsupported BG {bg}")


def read_secondary_index(path: Path):
    return json.loads((path / "index.json").read_text(encoding="utf-8"))


def secondary_by_config(index: dict):
    result = collections.defaultdict(list)
    for item in index["maps"]:
        for parent in item["parents"]:
            result[parent["config_id"]].append((item, parent))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--config-index", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--rendered-root", type=Path, default=DEFAULT_RENDERED)
    ap.add_argument("--secondary-dir", type=Path, default=DEFAULT_SECONDARY)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    secondary_index = read_secondary_index(args.secondary_dir)
    by_config = secondary_by_config(secondary_index)

    with args.config_index.open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))

    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True)

    results = []
    skipped = []

    for row in rows:
        secondary_pairs = [
            (int(ts), int(layout))
            for ts, layout in re.findall(
                r"t(\d+)/l(\d+)",
                row.get("secondary_configurations", ""),
            )
        ]
        if not secondary_pairs:
            continue

        config_id = row["config_id"]
        variant = int(row["map_variant"])
        if variant not in (1, 2):
            raise ValueError(
                f"{config_id}: secondary configuration uses variant {variant}"
            )

        primary = (
            int(row["primary_tileset_id"]),
            int(row["primary_layout_id"]),
        )
        primary_bg = variant
        secondary_bg = 3 - variant

        for secondary in secondary_pairs:
            candidates = [
                pair
                for pair in by_config.get(config_id, [])
                if (
                    pair[0]["tileset_id"],
                    pair[0]["layout_id"],
                ) == secondary
            ]
            if not candidates:
                raise ValueError(
                    f"{config_id}: no rendered secondary layer for {secondary}"
                )

            for secondary_meta, parent in candidates:
                parent_json = REPO / parent["map_json"]
                parent_meta = json.loads(
                    parent_json.read_text(encoding="utf-8-sig")
                )
                primary_png = parent_json.parent / parent_meta["output_png"]
                secondary_png = (
                    args.secondary_dir / secondary_meta["output_png"]
                )

                primary_rgba = np.asarray(
                    Image.open(primary_png).convert("RGBA")
                )
                secondary_rgba = np.asarray(
                    Image.open(secondary_png).convert("RGBA")
                )

                if primary_rgba.shape != secondary_rgba.shape:
                    skipped.append({
                        "config_id": config_id,
                        "variant": variant,
                        "primary_tileset_id": primary[0],
                        "primary_layout_id": primary[1],
                        "primary_size": [
                            int(primary_rgba.shape[1]),
                            int(primary_rgba.shape[0]),
                        ],
                        "secondary_tileset_id": secondary[0],
                        "secondary_layout_id": secondary[1],
                        "secondary_size": [
                            int(secondary_rgba.shape[1]),
                            int(secondary_rgba.shape[0]),
                        ],
                        "reason": (
                            "primary/secondary dimensions differ; "
                            "runtime scroll/wrap alignment not yet proven"
                        ),
                    })
                    continue

                primary_priority = priority_mask(
                    rom, primary[0], primary[1]
                )
                secondary_priority = priority_mask(
                    rom, secondary[0], secondary[1]
                )
                shape = primary_rgba.shape[:2]
                if (
                    primary_priority.shape != shape
                    or secondary_priority.shape != shape
                ):
                    raise ValueError(
                        f"{config_id}: priority/image shape mismatch"
                    )

                primary_rank = bg_rank(
                    primary_bg, primary_priority
                )
                secondary_rank = bg_rank(
                    secondary_bg, secondary_priority
                )
                primary_visible = primary_rgba[:, :, 3] != 0
                secondary_visible = secondary_rgba[:, :, 3] != 0
                overlap = primary_visible & secondary_visible

                choose_secondary = secondary_visible & (
                    ~primary_visible
                    | (secondary_rank > primary_rank)
                )

                composite = primary_rgba.copy()
                composite[choose_secondary] = secondary_rgba[
                    choose_secondary
                ]
                composite[~(primary_visible | secondary_visible)] = 0

                suffix = ""
                if len(candidates) > 1:
                    suffix = (
                        f"_pal{int(secondary_meta['palette_operand']):02X}"
                    )
                stem = (
                    f"{config_id}"
                    f"_sec_t{secondary[0]:02d}_l{secondary[1]:03d}"
                    f"{suffix}"
                )
                output_png = args.out_dir / f"{stem}.png"
                Image.fromarray(
                    composite.astype(np.uint8), "RGBA"
                ).save(output_png, optimize=True)

                stats = {
                    "primary_visible_pixels": int(primary_visible.sum()),
                    "secondary_visible_pixels": int(
                        secondary_visible.sum()
                    ),
                    "overlap_pixels": int(overlap.sum()),
                    "primary_wins_overlap": int(
                        (
                            overlap
                            & (primary_rank >= secondary_rank)
                        ).sum()
                    ),
                    "secondary_wins_overlap": int(
                        (
                            overlap
                            & (secondary_rank > primary_rank)
                        ).sum()
                    ),
                    "primary_high_priority_visible_pixels": int(
                        (
                            primary_visible
                            & (primary_priority != 0)
                        ).sum()
                    ),
                    "secondary_high_priority_visible_pixels": int(
                        (
                            secondary_visible
                            & (secondary_priority != 0)
                        ).sum()
                    ),
                }

                meta = {
                    "schema_version": 1,
                    "kind": "mode1_bg12_composite",
                    "config_id": config_id,
                    "variant": variant,
                    "primary": {
                        "tileset_id": primary[0],
                        "layout_id": primary[1],
                        "bg": primary_bg,
                        "map_json": str(parent_json.relative_to(REPO)),
                        "png": str(primary_png.relative_to(REPO)),
                        "png_sha256": sha256_file(primary_png),
                    },
                    "secondary": {
                        "tileset_id": secondary[0],
                        "layout_id": secondary[1],
                        "bg": secondary_bg,
                        "layer_json": str(
                            (
                                args.secondary_dir
                                / (
                                    Path(
                                        secondary_meta["output_png"]
                                    ).stem
                                    + ".json"
                                )
                            ).relative_to(REPO)
                        ),
                        "png": str(secondary_png.relative_to(REPO)),
                        "png_sha256": sha256_file(secondary_png),
                        "palette_operand": secondary_meta[
                            "palette_operand"
                        ],
                    },
                    "bgmode": 1,
                    "priority_order": [
                        "BG1_high",
                        "BG2_high",
                        "BG1_low",
                        "BG2_low",
                    ],
                    "includes": ["BG1", "BG2"],
                    "excludes": ["BG3", "OBJ"],
                    "image_width_px": int(composite.shape[1]),
                    "image_height_px": int(composite.shape[0]),
                    "stats": stats,
                    "output_png": output_png.name,
                    "output_png_sha256": sha256_file(output_png),
                }
                (args.out_dir / f"{stem}.json").write_text(
                    json.dumps(
                        meta, ensure_ascii=False, indent=2
                    ) + "\n",
                    encoding="utf-8",
                )
                results.append(meta)
                print(
                    f"composed {config_id}: "
                    f"primary BG{primary_bg} + "
                    f"secondary BG{secondary_bg}"
                )

    index = {
        "schema_version": 1,
        "kind": "mode1_bg12_composite_index",
        "composite_count": len(results),
        "skipped_count": len(skipped),
        "composites": results,
        "skipped": skipped,
        "policy": (
            "Only same-dimension primary/secondary pairs are composited. "
            "Output models BG1/BG2 only; BG3 and sprites are excluded."
        ),
    }
    (args.out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"complete: {len(results)} composites, "
        f"{len(skipped)} skipped configurations"
    )


if __name__ == "__main__":
    main()
