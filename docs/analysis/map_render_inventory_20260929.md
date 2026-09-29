# Map render inventory — 2026-09-29

## Coverage milestone

Every CF layout ID in the recovered table now has at least one rendered image:

    layout IDs 1..203
    unrendered = none

This does not mean every layout is proven reachable in normal gameplay. The inventory distinguishes canonical referenced maps from structural probes.

Master catalog:

    data/maps/rendered/catalog/map_render_catalog.csv
    data/maps/rendered/catalog/map_render_catalog.json

Generator:

    tools/python/build_map_render_catalog.py

## Current artifact inventory

The consolidated catalog contains 258 render artifacts:

| role | count |
|---|---:|
| normal primary | 145 |
| Mode-7 primary | 5 |
| opcode-0x51 immediate secondary layer | 50 |
| proven non-immediate secondary layer | 1 |
| Mode-1 BG1+BG2 composite | 52 |
| unreferenced structural probe | 5 |

The artifact count is larger than the number of layout IDs because the same layout may have multiple proven visual/resource states, secondary layers are preserved separately, and composites are configuration-level outputs.

## Referenced configuration coverage

Recovered configuration coverage:

    148 unique primary (tileset, layout) pairs
    49 unique immediate secondary pairs
    52 BG1+BG2 composite outputs
    0 skipped immediate-secondary configurations

All immediate secondary configurations now have a composite path, including the three unequal-dimension cases whose same-origin/no-wrap behavior was proven.

## Non-immediate TS42 secondary

Layout 164 is not truly unreferenced. Pack 0x9D contains a proven normal-mode non-immediate secondary selector:

    CC:FB61  50 2A A3 01   ; TS42 / layout 163 primary
    ...
    CC:FB93  11 28
    CC:FB98  51 2A A4      ; TS42 / layout 164 secondary

Canonical output:

    data/maps/rendered/dungeon_tileset_42_p28_secondary/map_164.png

The configuration-index builder focuses on immediate 0x51 pairs, so the master catalog records this as secondary_layer_non_immediate.

## Layouts without recovered selector references

Five layouts still lack a proven selector reference:

    17, 66, 79, 161, 162

All five nevertheless have strict structural render probes under data/maps/rendered/unreferenced_layout_probes/.

Layouts 17, 66 and 79 pass complete coverage with proven tileset-7 resources. Layouts 161 and 162 pass complete coverage with the inferred missing tileset-41 resource family. These images prove structural renderability, not gameplay reachability.

## Static-background completion

For normal Mode-1 configurations, canonical static geometry is now modeled as primary layer + optional secondary layer + SNES BG1/BG2 priority composition.

BG3 is intentionally not included in canonical full-map geometry because the normal map selector pipeline exposes only primary/secondary map pairs and binds those to BG1/BG2. Dynamic BG3 uses remain possible and are treated separately.

See:

    docs/analysis/bg12_map_composites_20260929.md
    docs/analysis/bg3_static_map_role_20260929.md

## Mode-7 coverage

Mode-7/EXTBG families are fully represented: TS1 layouts 1/2, TS2 layouts 3/4, and TS3 layout 5.

The world renderer applies the proven EXTBG rule where raw pixel bit 7 is priority rather than a palette-index bit. This removed the false magenta/high-palette colors previously visible in forest/tree/mountain detail.

## Catalog fields

The CSV/JSON catalog records artifact role, tileset/layout ID, config ID, variant, primary/secondary pair, BG assignment, palette operand, image dimensions, PNG/JSON paths, confidence, and provenance notes.

## Remaining map work

The large-scale geometry extraction phase is effectively complete. Remaining work is mainly semantic/runtime enrichment:

1. identify map names and locations from dialogue/event/warp evidence;
2. determine whether the five structural probes are truly unused or reached through non-standard setup paths;
3. export runtime-only BG3/OBJ/event overlays separately where useful;
4. retain alternate palette/visual states without replacing canonical geometry;
5. connect map images to event/warp/collision metadata for a navigable map database.
