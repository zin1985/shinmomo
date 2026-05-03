# Field / town mapchip pipeline after merge

## 方針

field / town / indoor は battle と違い、BG tilemap主導で復元する。

```text
VRAM tilemap entry
-> tile_id / palette / priority / hflip / vflip
-> tile usage
-> repeated 2x2 metatile
-> chunk
-> map preview PNG
```

## tilemap entry decode

```text
tile     = entry & 0x03FF
palette  = (entry >> 10) & 0x07
priority = (entry >> 13) & 0x01
hflip    = (entry >> 14) & 0x01
vflip    = (entry >> 15) & 0x01
```

## metatile

初期運用では 2x2 を正本候補とする。4x4以上は建物/装飾/chunk候補として別管理。

## 出力

```text
data/csv/field_metatile_candidates_after_merge.csv
graphics/field/reconstructed_map_preview_after_merge.png
```
