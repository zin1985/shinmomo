# Shinmomo structural world viewer

Structural map, event, transition and NPC viewer. Full-map PNG is not the primary data model.
Canonical assets are local-only; `public_redrawn` uses the same structure with replacement art and no canonical fallback.

## Local preview

From the repository root:

```bash
python tools/python/build_structural_world_viewer.py
python -m http.server 8000
```

Then open `http://localhost:8000/viewer/`.

The canonical profile loads local rendered map PNGs from `data/maps/rendered/...` and overlays static character selector sprites.
The actor placement layer is intentionally marked provisional: opcode `0x59` `field0659/field0699` seed pairs are plotted against each map's structural grid, not yet treated as universally proven coordinate fields.
The builder records a corpus bounds audit in `world.json`; the 2026-09-30 corpus places every current static actor seed inside its mapped structural map bounds.
