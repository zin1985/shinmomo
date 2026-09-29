# Mode-1 BG1/BG2 map composites — 2026-09-29

## Result

Primary normal-map renders and proven opcode-0x51 secondary layers can now be
combined using the SNES Mode-1 BG1/BG2 priority rules.

Canonical output directory:

```text
data/maps/rendered/bg12_composites/
```

Renderer:

```text
tools/python/render_bg12_map_composites.py
```

The current batch contains:

- 49 composite PNGs;
- 49 same-name JSON metadata files;
- one `index.json`;
- 3 skipped configuration occurrences whose primary/secondary dimensions differ.

These are **BG1+BG2 background composites**, not complete screenshots.  BG3,
sprites/OBJ, windows, color math and event objects are intentionally not
flattened into these images.

## BGMODE proof

Normal-map initialization selects Mode 1 through the WRAM BGMODE mirror
`$0376`.

At `80:CB60`:

```text
LDA #$01
JSL $80:A065
```

and the same Mode-1 selection appears at `80:CBCD`.

`80:A065` preserves the upper BGMODE control bits and replaces the low three
mode bits:

```text
STA $00
LDA $0376
AND #$F8
ORA $00
STA $0376
RTL
```

One normal initialization path also enables the Mode-1 BG3-priority option via
`80:A0A3`.  That changes BG3's position in the priority stack, but does not
change the relative BG1/BG2 ordering used by this renderer.

## Primary/secondary BG assignment

`80:C6A8` copies the PPU screen-base registers into WRAM mirrors:

```text
BG1SC -> $1142
BG2SC -> $1144
BG3SC -> $1146
BG4SC -> $1148
```

`80:C6FD` stores the selected layer number in `$0302`, subtracts one,
multiplies by two, and indexes the table beginning at `$1142`.

Therefore:

```text
selector 1 -> BG1
selector 2 -> BG2
selector 3 -> BG3
```

Primary setup `80:CD85` passes the map variant directly to `80:C6FD`.

Secondary setup `80:CDD1` passes `3 - variant` to `80:C6FD`.

All recovered immediate-secondary configurations use variant 1 or 2, so the
assignment is unambiguous:

| map variant | primary | secondary |
|---:|---|---|
| 1 | BG1 | BG2 |
| 2 | BG2 | BG1 |

## Tile priority

Expanded normal-map tilemap words are standard SNES BG tilemap entries.
Bit `0x2000` / bit 13 is the tile priority flag.

For Mode 1, considering BG1 and BG2 only, the relative order is:

```text
BG1 high
BG2 high
BG1 low
BG2 low
```

At each non-transparent pixel the composite renderer compares the BG assignment
and tile priority from the ROM-derived expanded tilemap and selects the visible
BG1/BG2 pixel accordingly.

Transparent color-index-zero pixels remain transparent and expose the other
layer when present.

## Origin / scrolling

The secondary update path adds values derived from `$1516/$1518` while
building the currently resident tilemap window.

Those bytes are the high bytes of the 16-bit scrolling accumulators
`$1515/$1517`; the C1 movement/update logic modifies those accumulators at
runtime.  They are therefore current scroll/window state, not a fixed static
secondary-map origin.

For equal-dimension primary/secondary layouts, the canonical full-map layers
share the same zero-scroll origin and are composited at (0,0).

Dimension-mismatched configurations remain fail-closed because wrapping/window
alignment across unequal map extents has not yet been proven.

## Skipped dimension-mismatched configurations

Three configuration occurrences are intentionally not flattened:

```text
cfg_t08_l096_v2:
  primary t08/l096 = 768 x 1024
  secondary t08/l093 = 2304 x 1024

cfg_t23_l123_v1:
  primary t23/l123 = 3328 x 1024
  secondary t23/l124 = 2816 x 1024

cfg_t23_l123_v2:
  primary t23/l123 = 3328 x 1024
  secondary t23/l124 = 2816 x 1024
```

Their separate primary and secondary RGBA layers remain canonical and usable.

## Palette-state multiplicity

`t14/l105 -> t14/l106` has two proven parent resource/palette states.
Both are preserved as separate composites rather than selecting one by
appearance.

This is why 48 same-dimension configuration occurrences produce 49 composite
PNGs.

## Validation

The composite tool consumes:

1. the canonical ROM-derived primary map PNG/JSON;
2. the canonical ROM-derived opcode-0x51 secondary layer PNG/JSON;
3. the ROM-derived expanded primary/secondary tilemaps for priority bit 13;
4. configuration-index map variant for BG assignment.

No emulator screenshot, runtime VRAM, runtime CGRAM, savestate or SRAM is used
to create the composite images.

Representative contact-sheet inspection shows the secondary layer restoring
water surfaces, cliff/building outlines, vegetation/foreground detail and other
map structure that was absent from primary-only renders.

## Next work

1. prove wrap/alignment for the three unequal-dimension configuration
   occurrences;
2. identify whether BG3 carries any map-static content worth exporting;
3. keep sprite/event/object layers separate from canonical background geometry;
4. continue human-facing place-name binding without altering recovered map
   geometry.
