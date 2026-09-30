# Native map movement bounds catalog

Updated: 2026-09-30

Normal VM opcode `0x52` at `C4:8B16` writes its four normal-form operands to `$15CA..$15CD`. Static caller tracing proves these are inclusive min-X, max-X, min-Y, max-Y movement bounds consumed by `C1:8943 -> 81:81DD`.

The conservative catalog starts from the confirmed primary-selector corpus and follows only instruction-bounded post-selector prefixes. It finds **155 selector occurrences / 106 unique configurations / 122 packs**. Four configurations have multiple distinct movement windows, so bounds remain occurrence-level metadata rather than layout-size metadata.

## Priority anchors

```text
旅立ちの村 / cfg_t04_l008_v2
CC:1C3F  50 04 08 02
CC:1C43  15 00 0C
CC:1C46  52 09 46 08 37
=> X=9..70, Y=8..55
```

These values exactly match the independent Remote Lab WRAM capture.

```text
cfg_t07_l015_v2 / pack 0x2E
CB:DE70  50 07 0F 02
CB:DE74  52 00 13 00 0C
=> X=0..19, Y=0..12
```

The known forward transition enters this room at `(9,12)`. The decoded structural layer has a three-cell central floor opening at `x=8..10,y=12`, centered on `(9,12)`. Runtime evidence independently confirms that walking south through the central exit returns to pack `0x50`. This explains the reverse edge as native out-of-bounds saved-state return rather than an unidentified VM transition opcode.

Exact runtime pre-exit X was not captured, so `x=8..10,y=12` remains a strong candidate corridor, not a confirmed three-cell passability claim.

## Outputs

- `data/maps/transitions/map_native_bounds_catalog.csv`
- `data/maps/transitions/map_native_bounds_summary.json`
- `data/maps/transitions/pack2e_south_boundary_to_tabidachi_20260930.json`
- `tools/python/catalog_map_native_bounds.py`
