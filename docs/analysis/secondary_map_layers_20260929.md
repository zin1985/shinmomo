# Opcode-0x51 secondary map layers — 2026-09-29

## Result

All immediate secondary configurations recorded in the recovered map
configuration index now have ROM-derived RGBA layer images.

Canonical output:

```text
data/maps/rendered/secondary_layers/
```

Renderer:

```text
tools/python/render_secondary_map_layers.py
```

Totals:

- 49 unique secondary `(tileset, layout)` pairs;
- 50 PNGs because tileset 14 / layout 106 has two proven parent palette states;
- 0 strict-render failures.

## Why these are exported separately

Normal-map selector opcode `0x50` establishes the primary map configuration.
Immediate opcode `0x51` occurrences establish a secondary tileset/layout while
the already-loaded graphics and palette state remains in effect.

The resulting images are generally sparse: contours, water/detail lines,
decorative foreground/background fragments and other partial geometry.  This is
consistent with a secondary BG-layer role rather than a separate standalone
location.

The repository therefore stores these as **secondary layers**, not as complete
composited maps.

Exact BG1/BG2 priority composition is intentionally deferred until the normal
PPU layer-order state and tile priority bits are modeled together.  A naive
"secondary always over primary" composite is not treated as canonical.

## Resource inheritance

Each secondary render inherits the exact proven ROM resource state from the
primary configuration that immediately precedes it:

- opcode-0x10 graphics resources;
- opcode-0x33 explicit VRAM placements where present;
- proven transition zero-fill ranges where present;
- opcode-0x11 palette resource.

The secondary layout is then expanded with its own secondary tileset ID and
validated against that inherited VRAM/CGRAM state.

Every committed secondary image passes:

1. complete CHR coverage;
2. complete non-zero palette coverage;
3. normal-BG color-zero transparency handling.

## Size relationship

Of the 49 unique secondary pairs:

- 48 have the same pixel dimensions as their parent primary layout;
- tileset 23 / layout 124 is the only size mismatch:
  - secondary: 2816 x 1024
  - parent tileset 23 / layout 123: 3328 x 1024

This makes layout 124 the main alignment exception for later composite work.

## Palette variants

Tileset 14 / layout 106 is reachable from a primary layout-105 family with two
proven palette states.  Both are preserved:

```text
t14_l106_pal0E_v1.png
t14_l106_pal11_v2.png
```

No palette choice is silently discarded.

## Coverage after this batch

The CF layout table contains 203 layout IDs.

Recovered references now account for:

- 148 primary layout IDs;
- 49 secondary-only layout IDs;
- 197 referenced layout IDs total.

Only six layout IDs currently have no recovered primary or immediate-secondary
reference:

```text
17, 66, 79, 161, 162, 164
```

Those six are the next map-output investigation target.  They are not assumed
unused until all other reference mechanisms are checked.

## Policy

- ROM bytes and runtime raw captures are not committed.
- Runtime evidence may validate behavior but committed images are reconstructed
  from ROM resources.
- Secondary layers remain separate until layer priority/alignment is proven.
