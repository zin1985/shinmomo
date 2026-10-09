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

## Transition tiers

The viewer imports every row from `data/maps/transitions/map_transition_candidates.csv`.

- Tier 1: `confirmed` rows become solid map edges when both source and destination configs are known.
- Tier 2: `strong_candidate` rows become dashed map edges when both configs are known.
- Tier 3: rows with unresolved `source_config_id` are never guessed from `script_pack`; when the destination config is known they appear under **Unbound transitions** on that destination map.

Clicking an edge or unbound row shows trigger metadata, event record, destination pack/entry, arrival X/Y, confidence, evidence and provenance. Bound edges also provide an **open map** control. As transition analysis fills `source_config_id`, rebuilding `world.json` automatically promotes eligible rows from the unbound panel to map edges.

## Dungeon previews and actor facing

Dungeon `normal_primary` catalog rows may omit explicit pixel dimensions. The viewer builder recovers those dimensions from the structural metatile grid at 16 pixels per cell, so existing t05+ dungeon PNGs are no longer rendered into a zero-sized stage.

When a BG1+BG2 composite exists for a configuration, the canonical viewer preview prefers that composite while retaining both structural layers.

Static selector catalog thumbnails keep the original animation base metadata unchanged. For group 2/3 selectors that expose four consecutive directional states, the representative viewer artwork uses the first frame of `base_state + 1`, matching the established right / down(front) / left / up(back) ordering. This is a display choice, not a rewrite of the actor's animation state.

## Actor dialogue windows

The viewer imports `data/npc_display/static_actor_event_dialogue_binding_20260930.csv` and links rows back to static opcode-0x59 actors by configuration, record ID and selector.

Clicking an actor opens a game-style dialogue window above the sprite. Multiple event-source branches remain selectable instead of being collapsed into one representative line. Historical decoded text keeps its embedded line breaks; quote-delimited blocks are exposed as candidate pages for browser playback. These page boundaries are explicitly marked as decoder-derived candidates unless later runtime/static evidence confirms exact in-game pagination.

The same actor payload now also carries sprite semantic and four-direction metadata from the dedicated sprite catalogs.

## Source transition hotspots

The viewer imports `data/maps/transitions/source_transition_hotspots.csv`. Resolved source rectangles are clickable on the map when transitions are enabled. A hotspot with a resolved destination config opens that map directly and highlights/centers the resolved destination arrival coordinate when available. Source coordinates are never inferred from script-pack identity.


## Event-aware transition gating (2026-10-10)

Bound transitions expose a derived activation_gate. evaluation=unknown is
intentional: static or runtime-observed transitions are not necessarily
executable in the current story phase. Source hotspots and native saved-return
contexts carry source-region and return-stack provenance without inventing a
true/false flag predicate. The "inspect map" button is a research preview,
not a simulation of permitted movement. Native C1:8955 exits are keyed by
unique source/destination edges plus proven saved return origin, never by
shared handler address alone. See
docs/analysis/native_saved_return_graph_gate_20261010.md.


## Research-only spatial gates and phase ambiguities

The Viewer displays VM source hotspot coordinate predicates and makes a
**tri-state distinction** for selected research coordinates: outside a proven
trigger region is incompatible with that trigger; inside matches its
coordinate clause but never proves the transition can fire. Current story
flags, control-flow branches, and actual emulator position remain unresolved.
The five pack-0xCE destination configuration candidates for CC:1160 are shown
together without a synthetic graph edge or an invented phase selector.

Source-unbound investigation queue:
data/maps/transitions/source_unbound_investigation_queue.json
Evidence memo: docs/analysis/transition_spatial_phase_source_triage_20261010.md.
