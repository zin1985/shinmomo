# Mapchip canonicalization spec（2026-05-03）

## Input

- decoded BG tilemap CSV
- optional CGRAM
- optional DMA sequence id

## 2x2 extraction

```text
tile00 tile01
tile10 tile11
```

## Keys

```text
shape_key  = tile00,tile01,tile10,tile11
render_key = tile ids + palette + hflip + vflip + priority
canonical_key = normalized tile set + adjacency signature
```

## Output

```csv
scene,metatile_id,canonical_key,variant_count,palette_variants,flip_variants,usage_frequency,notes
```
