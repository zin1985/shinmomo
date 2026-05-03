# Final data layout spec（2026-05-03）

## maps

```text
data/maps/{scene}/map_grid.csv
data/maps/{scene}/metatile_dictionary.csv
data/maps/{scene}/metatile_graph.csv
data/maps/{scene}/palette_mapping.csv
data/maps/{scene}/validation_report.csv
```

## sprites

```text
data/sprites/{scene}/entity_table.csv
data/sprites/{scene}/animation_table.csv
data/sprites/{scene}/chr_usage.csv
data/sprites/{scene}/oam_chr_mapping.csv
```

## graphics

```text
graphics/{scene}/bg1.png
graphics/{scene}/bg2.png
graphics/{scene}/bg3.png
graphics/{scene}/oam.png
graphics/{scene}/composited.png
graphics/{scene}/metatile_contactsheet.png
```

## runtime logs

```text
data/runtime_logs/{session}/vram.bin
data/runtime_logs/{session}/cgram.bin
data/runtime_logs/{session}/oam.bin
data/runtime_logs/{session}/bg_summary.csv
data/runtime_logs/{session}/dma_trigger_log.csv
data/runtime_logs/{session}/visible_objects.csv
```
