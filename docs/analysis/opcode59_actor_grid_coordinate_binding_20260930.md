# Opcode 0x59 actor grid-coordinate binding

Date: 2026-09-30

## Result

For the opcode `0x59` actor/controller rendering path, the two bytes stored in
`$0659,X` and `$0699,X` are statically confirmed as map-grid X/Y coordinates.

This statement is intentionally handler-local. The WRAM object/controller pool is
shared and the same columns can have other meanings in other handlers.

## Static path

The opcode `0x59` event command stores its operands through the standard controller
constructor. The relevant actor renderer later executes:

```
C1:B07E  LDA $0659,X
C1:B081  STA $030B
C1:B084  LDA $0699,X
C1:B087  STA $030D
C1:B08A  JSL $81:B10F
```

At `81:B10F`, the first axis is converted as:

```
$030B - $1573 + 7
AND #$00FF
ASL x4
```
The second axis is converted equivalently from `$030D` relative to `$157D`,
with the renderer's Y adjustment, then stored as a 16-bit render position.

Therefore the renderer converts the two controller bytes to screen/render positions
by multiplying grid deltas by 16 pixels. This directly supports X/Y map-grid semantics
for this actor path.

## Corpus check

The structural viewer joins opcode `0x59` actors to their mapped configurations.
Current corpus:

- actor rows: 817
- inside mapped structural grid: 817
- outside mapped structural grid: 0
- mapped configurations: 75

This bounds result is supporting evidence, not the primary proof. The primary proof
is the renderer code path above.

## 旅立ちの村 visual validation

`cfg_t04_l008_v2` / pack `0x50` contains 10 current static actor records.
The exact-grid composite places all ten anchors on plausible village actor locations:
fields, paths, building fronts, and the north facility area. None lands in the remote
forest-only background or outside the village map.

Validation images:

- `graphics/viewer_validation/tabidachi_static_actor_overlay_grid_exact.png`
- `graphics/viewer_validation/tabidachi_actor_arrival_overlay.png`

The combined image also plots the three grouped resolved arrival coordinates currently
known for this map: (29,55), (34,49), and (39,37).

Selector graphic aliases are resolved through
`static_character_selector_catalog_20260930.csv:duplicate_of`; for example selector
`0x59` reuses `0x3F` graphics and `0x5A` reuses `0x15`.

## Remaining uncertainty

The map-grid coordinate itself is confirmed for the opcode `0x59` actor renderer.
The exact visual-origin offset of the reconstructed catalog sprite image is not yet
proven, so the HTML viewer uses a bottom-center artwork anchor and reports that
separately from coordinate confidence.
