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

The current output contains:

- 52 composite PNGs;
- 52 same-name JSON metadata files;
- one `index.json`;
- zero skipped immediate-secondary configurations.

These are **BG1+BG2 background composites**, not complete screenshots. BG3,
sprites/OBJ, windows, event objects and other runtime-only effects remain
separate.

## BGMODE proof

Normal-map initialization selects Mode 1 through the WRAM BGMODE mirror
`$0376`.

At `80:CB60`:

```text
LDA #$01
JSL $80:A065
```

and the same Mode-1 selection occurs at `80:CBCD`.

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

One normal initialization path also enables the Mode-1 BG3-priority option.
That changes BG3's place in the complete PPU priority stack but does not change
the relative BG1/BG2 order used by this background-only renderer.

## Primary / secondary BG assignment

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
Bit `0x2000` / bit 13 is the tile-priority flag.

For Mode 1, considering BG1 and BG2 only, the relative order is:

```text
BG1 high
BG2 high
BG1 low
BG2 low
```

At every non-transparent pixel the renderer compares BG assignment and tile
priority, then selects the visible BG1/BG2 pixel.

Color-index-zero pixels remain transparent and expose the other layer.

## Shared origin proof

The secondary current-map coordinates are stored at `$15C3/$15C4`.
Normal transition and restore paths initialize them to the same position as the
primary current-map coordinates `$1573/$157D`.

There is a dedicated VM command for introducing a different secondary origin:

```text
opcode 0x62 -> handler C4:9217
```

Its handler explicitly computes:

```text
$15C3 = $1573 + operand_x
$15C4 = $157D + operand_y
```

None of the three formerly dimension-mismatched configuration streams uses
opcode `0x62`.

Therefore their static primary and secondary layouts share top-left origin
`(0,0)`.

## No-wrap proof for the unequal-size cases

`A0:D01A` converts current map coordinates into layout-cell addresses.

Normally it range-checks the coordinate against the active primary or secondary
layout dimensions. An optional special path first masks coordinates:

```text
if ($0307 & 0x10):
    x &= $15CB
    y &= $15CD
```

The four `$15CA..$15CD` values are populated by VM opcode `0x52`.

`$0307` itself is explicitly set by VM opcode `0x64` (handler
`C4:92A9`). In the relevant configuration streams the observed `0x64`
operands are `0x24` and `0x04`; neither sets bit `0x10`.

Thus the special mask/wrap path is not active for these configurations.

When a secondary coordinate is outside that layout's normal bounds,
`A0:D01A` marks it invalid with `$13A4 = 0xFE`. Downstream
`A0:CFF4` emits zero tilemap entries for that invalid area.

This proves the static unequal-size rule:

- same top-left origin;
- if secondary is larger than primary, clip it to the primary extent;
- if secondary is smaller than primary, pad the uncovered primary extent with
  transparent/zero secondary pixels;
- do not tile or wrap the secondary image.

## Formerly mismatched configurations now resolved

### cfg_t08_l096_v2

```text
primary   t08/l096 = 768 x 1024
secondary t08/l093 = 2304 x 1024
```

The composite uses the leftmost 768-pixel portion of the secondary at shared
origin.

### cfg_t23_l123_v1

```text
primary   t23/l123 = 3328 x 1024
secondary t23/l124 = 2816 x 1024
```

The secondary is placed at shared origin. The remaining 512 pixels on the
right are primary-only because secondary coordinates are out of range.

### cfg_t23_l123_v2

The same geometry rule applies; only the BG1/BG2 assignment changes with
variant 2.

These three configurations are allow-listed in the renderer because their
same-origin/no-wrap behavior is now proven. Any future unknown dimension
mismatch remains fail-closed.

## Runtime scrolling versus static origin

The secondary update path adds values derived from `$1516/$1518` when
building the resident tilemap window.

Those bytes are the high bytes of the 16-bit scrolling accumulators
`$1515/$1517`; the C1 movement/update logic modifies them during play. They
describe the current resident-window scroll state, not a persistent static
offset between the two source layouts.

The canonical composite therefore represents the zero-scroll source-map
geometry.

## Palette-state multiplicity

`t14/l105 -> t14/l106` has two proven parent resource/palette states.
Both are retained rather than selecting one by appearance.

This is why the recovered immediate-secondary configuration set produces 52
composite PNGs rather than a one-image-per-secondary-pair count.

## Validation

The composite tool consumes:

1. canonical ROM-derived primary map PNG/JSON;
2. canonical ROM-derived opcode-0x51 secondary layer PNG/JSON;
3. ROM-derived expanded primary and secondary tilemaps for priority bit 13;
4. configuration-index map variant for BG assignment.

No emulator screenshot, runtime VRAM, runtime CGRAM, savestate or SRAM is used
as rendering input.

Representative inspection shows the secondary layer restoring water surfaces,
cliff/building outlines, vegetation and foreground detail that is absent from
primary-only renders.

## Status

All currently recovered immediate opcode-0x51 secondary configurations now have
a BG1/BG2 composite rendering path.

Remaining map-output refinements are:

1. identify whether BG3 carries map-static content worth exporting;
2. keep sprite/event/object layers separate from canonical background geometry;
3. continue semantic place-name/event binding without altering recovered
   geometry.
