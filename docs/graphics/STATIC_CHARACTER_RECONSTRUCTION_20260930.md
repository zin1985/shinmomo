# Static character reconstruction from ROM — 2026-09-30

## Result

Character/NPC graphics can now be reconstructed from the ROM without a runtime VRAM or CGRAM dump.

The recovered static chain is:

```
display selector
 -> 5-byte display record
 -> sprite group + animation state seed
 -> CHR resource id + CHR window id + palette resource id
 -> context-5 graphics descriptor
 -> ROM compressed CHR stream
 -> dispatch-0 decompression
 -> B893 OBJ tile packing
 -> B294 frame pieces
 -> static palette resource
 -> PNG
```

Runtime capture is now needed mainly for semantic binding and validation, not for the graphics bytes themselves.

## Five-byte display selector record

The table begins at ROM physical offset `0x000000` and is indexed as
`selector * 5`.

For the actor families validated here, the record behaves as:

| byte | role |
| ---: | --- |
| 0 | CHR resource id passed through the BC89 resource loader |
| 1 | group-specific CHR window selector, resolved through B2EE |
| 2 | animation state seed/base |
| 3 | sprite group / attribute byte; low nibble is B294/B2C1 group |
| 4 | palette/resource id passed through BCA3 |

The B2EE window selector resolves to two bytes:

```
source_tile_start
tile_count
```

Those values match the live resource-cache fields `$1122/$1121`.

## Context-5 actor graphics descriptors

The village actor resources observed at runtime use graphics context 5.
`C0:BAAC[5]` resolves the descriptor base to `C3:0678`.

Validated examples:

| resource | ROM source | decoded bytes |
| ---: | --- | ---: |
| 1 | D9:0000 | 0x07C0 |
| 8 | D9:1DF8 | 0x0500 |
| 29 | D9:71FE | 0x1000 |
| 42 | D9:E689 | 0x0F80 |

All use the already-proven dispatch-0 ring/LZSS decoder path for the data tested here.

## B893 OBJ tile packing

A decoded sequential CHR run is not copied linearly into OBJ tile-number order.
The observed and byte-verified mapping is:

```
decoded tile 0  -> local OBJ tile 0
decoded tile 1  -> local OBJ tile 16
decoded tile 2  -> local OBJ tile 1
decoded tile 3  -> local OBJ tile 17
...
```

Equivalently:

```
local_tile = (j // 2) + (16 if j is odd else 0)
```

The selected source run begins at the B2EE `source_tile_start`.

## Byte-level validation against live VRAM

The static decoder was compared with the already captured village runtime VRAM:

| actor/example | resource | source window | exact tiles |
| --- | ---: | --- | ---: |
| Momotaro | 1 | 0 + 18 | 18 / 18 |
| Ginji CHR family | 8 | 0 + 16 | 16 / 16 |
| group2 elder NPC | 29 | 96 + 16 | 16 / 16 |
| group3 red-hat NPC | 29 | 16 + 16 | 16 / 16 |
| group3 purple/green NPC | 29 | 64 + 16 | 16 / 16 |
| group7 blue NPC | 42 | 0 + 8 | 8 / 8 |

No CHR tile mismatch remains for these six examples.

## Static palette validation

Context-5 palette resource 1 resolves to:

```
descriptor C0:4A89
destination CGRAM index 128
32 colors
```

Its 64 payload bytes match the runtime game-side WRAM palette staging buffer
exactly: **32 / 32 BGR555 colors**.

## Important consequence

The runtime `$0DA5/$0DE5` value is not character identity. It is the relative
tile displacement produced after dynamic resource allocation.

For static reconstruction, the stable identity chain is instead:

```
selector
 + CHR resource
 + CHR window
 + sprite group
 + animation state seed
 + palette resource
```

This removes dynamic VRAM allocation from the reconstruction problem.

## Viewer representative orientation

`build_static_character_catalog.py` now reads the resolved directional catalog when choosing
the single representative PNG used by the HTML viewer. Confirmed drawable directional
selectors use the first front/down frame instead of blindly using the selector base state.
This extends the earlier group-2/group-3 front preference to visual-confirmed group-4/5/7
families without forcing shared-family selectors whose own CHR windows cannot draw those
frames.

After regeneration, the static viewer corpus still contains 817 opcode-59 actors.
The established group-2/group-3 representative-frame behavior is deliberately unchanged.
For the newly visual-confirmed group-4/5/7 selectors, 39 mapped actor rows now explicitly
carry `front_from_directional_catalog`; their representative frame is the proven front/down
state rather than the selector base state. The remaining pose/special/direction-invariant
families are not promoted to four-direction actors.

This fixes the newly resolved sideways NPC thumbnails without broad, unrelated sprite-image
churn or pretending that non-directional objects have a facing direction.

## Current known selector examples

- `0x01`: resource 1, group 2, state seed 1, Momotaro
- `0x0D`: resource 8, group 2, state seed 52, Ginji CHR family
- `0x24`: resource 29, group 2, state seed 216, runtime-confirmed elder village NPC family
- `0x40`: resource 29, group 3, state seed 5, runtime-confirmed red-hat NPC family
- `0x3F`: resource 29, group 3, state seed 17, runtime-confirmed purple/green NPC family
- `0x7D`: resource 42, group 7, state seed 6, runtime-confirmed blue NPC family

The exact semantic actor id -> selector binding should continue to be kept
separate from graphics reconstruction unless runtime/event logic proves it.
