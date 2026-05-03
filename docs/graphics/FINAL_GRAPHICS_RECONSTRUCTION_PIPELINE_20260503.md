# Final graphics reconstruction pipeline（2026-05-03）

## Pipeline

```text
1. Lua runtime logging
2. dma_sequence segmentation
3. VRAM grouping
4. BG tilemap decode
5. 2x2 metatile extraction
6. canonicalization
7. metatile graph build
8. deterministic layout reconstruction
9. CGRAM apply
10. BG/OAM layer separation
11. PNG / CSV / JSON export
```

## Input files

```text
vram.bin
cgram.bin
oam.bin
ppu_registers.csv
dma_trigger_log.csv
bg_summary.csv
visible_objects.csv
active_object_list.csv
frame_summary.csv
```

## Output files

```text
data/maps/{scene}/map_grid.csv
data/maps/{scene}/metatile_dictionary.csv
data/maps/{scene}/metatile_graph.csv
data/maps/{scene}/palette_mapping.csv
data/maps/{scene}/validation_report.csv
graphics/{scene}/bg1.png
graphics/{scene}/bg2.png
graphics/{scene}/oam.png
graphics/{scene}/composited.png
```

## Guarantee target

```text
same input logs -> same reconstructed map / sprite output
```

This is the target state. Full scene validation still needs fresh logs.
