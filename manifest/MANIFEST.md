# Manifest 260510Y

## Included text files

```text
README.md
NOT_INCLUDED_ROM.txt
COMMIT_COMMANDS_260510Y.sh
docs/handoff/HM_260510Y.md
docs/analysis/goals.md
docs/analysis/core_g13.md
docs/analysis/core_vm.md
docs/analysis/core_patch.md
docs/analysis/graphics_g13.md
docs/analysis/graphics_bridge.md
docs/analysis/graphics_topology.md
docs/analysis/graphics_cluster.md
docs/analysis/findings.md
manifest/MANIFEST.md
manifest/EXCLUDED.md
```

## Included CSV schema / summary files

```text
data/runtime/goal_progress.csv
data/runtime/g13_mask_minimal.csv
data/runtime/g13_cutoff.csv
data/runtime/g13_contrib.csv
data/runtime/g13_pretrigger.csv
data/runtime/frame.csv
data/runtime/visible.csv
data/runtime/cluster_track.csv
data/runtime/oam_attr.csv
data/runtime/dma.csv
data/bg/tilemap_world.csv
data/bg/metatile.csv
data/battle/chr_atlas.csv
```

## Included tool stubs

```text
tools/python/g13_extract.py
tools/python/g13_filter.py
tools/python/density.py
tools/python/cluster_track.py
tools/python/metatile.py
tools/python/dma_summary.py
tools/lua/rt_logger.lua
```

## Exclusion guarantee

This package intentionally excludes ROM binaries, raw VRAM/OAM/CGRAM dumps, savestates, and nested archives.

