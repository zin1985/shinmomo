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
For the opcode `0x59` actor-renderer path, `field0659/field0699` are now statically confirmed as map-grid coordinates: the renderer copies them to `$030B/$030D`, and `81:B10F` converts those values to 16px render coordinates relative to the camera/grid origin.
This is handler-local evidence and does not assign universal coordinate semantics to the shared WRAM columns `$0659/$0699`.
The builder records a corpus bounds audit in `world.json`; the 2026-09-30 corpus places all 817 current static actor seed pairs inside their mapped structural map bounds.
Sprite artwork is drawn with a viewer bottom-center anchor approximation; the coordinate itself is stronger evidence than the exact artwork-origin offset.

The optional `arrival points` layer plots destination coordinates from the static transition catalog when both destination configuration and X/Y are resolved. Identical destination pack/entry/X/Y points are grouped to avoid duplicate markers. Rows whose source map is unresolved remain destination-only markers; the viewer never guesses a source map from script-pack identity.
