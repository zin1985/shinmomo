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


## Coordinate-dependent native saved-return arrivals (2026-10-11)

The existing Tabidachi village -> world native saved-return edge now
carries TWO separately runtime-confirmed exact source/arrival pairs:
(28,55)->(54,237) and (29,55)->(55,237). They are NOT an
extrapolated formula or a proven full-width exit corridor. Selecting
the map without a grounded source coordinate does not arbitrarily
focus the previous representative arrival (54,237). The edge remains
a research preview; saved return stack and story state are not
automatically evaluated. Evidence:
docs/analysis/tabidachi_world_coordinate_variants_20261011.md.


## Spatially verified movement on strong static VM candidates

Two existing candidate transition edges now show a separate runtime
movement evidence hint. Sources: village (29,17) -> interior (9,12),
and world (52,233) -> another map (17,37). The app does NOT change
their strong_candidate opcode confidence, or treat a source coordinate
as a universal story predicate. The CPU instruction PC is unproven.
See docs/analysis/runtime_spatial_two_entrances_20261011.md.


## Runtime native return from pack 0x4D to world (2026-10-11)

A new, independent 57th Viewer edge now represents the actually
observed south-boundary saved-map return from cfg_t04_l006_v2
(17,37) to world cfg_t01_l001_v1 (52,233). The source native bounds
are x1..46/y1..37; crossing at x17,y38 and the return at emulator
frame 663387 were verified by frame-end WRAM. This is NOT a
captured VM0x56 execution event and story predicates remain unknown.
Do not generalize the one confirmed exit cell to the entire corridor.
See docs/analysis/pack4d_world_native_return_20261011.md.


## Confirmed in-game title for pack 0x4D (2026-10-11)

A hidden BizHawk screenshot, with WRAM pack 0x4D at (17,37),
shows the actual place title 桃太郎の生家. Viewer auto-selects
pack 0x4D on cfg_t04_l006_v2 and displays the pack-scoped title;
other configurations sharing tileset or layout are NOT renamed.
Raw screenshot is local-only; provenance SHA256 is in
data/maps/context/pack4d_runtime_location_title_20261011.json.
See docs/analysis/pack4d_title_and_dungeon_frontier_20261011.md.


## Dungeon おむすびころりん, source cheat explicitly disclosed

World pack4C x47,y200 was reached with a local analysis-only
WRAM coordinate cheat, then actual SNES Up entered the independently
cataloged world hotspot (47..48,199) to pack0x91. Frame-end WRAM
proves switch at 663079 and stable cave arrival (71,59) at 663203.
A later screenshot shows the in-game title おむすびころりん.
The existing catalog_transition_0750 now carries this exact landing
and a prominent cheat-origin annotation, NOT normal world walkability
or story activation. No new edge or confidence promotion.
Data: data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json.


## Cave Omusubi-kororin hole, shaft and pack0x95 transition

Two additional bound connections are now represented by event-specific
and saved-map-context-specific evidence, not universal story predicates.
From cave pack91 (71,61), the gamepad Up enters (71,59), returning to
the prior cheated world saved-map origin (47,199) in pack4C.
A second research cheat positions within pack91 at (75,54), directly
south of a black hole tile. Real gamepad Up triggers the hole (75,53),
transports the player to (70,8), automatically descends to (70,26)
without input, then real Right switches pack91->pack95, arriving
(22,8). The preexisting ROM destination candidate
catalog_transition_0171 is given a runtime-confirmed source
cfg_t08_l092_v2; CC:D377 remains a *candidate*, never a captured PC.
Viewer now includes 149 maps, 59 bound edges, 1297 candidates.
See docs/analysis/omusubi_cave_return_hole_and_pack95_20261011.md.


## Pack0x95 reverse stair back to cave pack0x91

Real gamepad Down from pack95(22,8) to(22,9), then Up onto the
original arrival stair tile (22,8), causes pack95->pack91 switch at
664110 and stable return to cave (71,26) at 664196, followed by 152
stable observation frames. The unique existing ROM candidate
catalog_transition_0194 is now bound to runtime source
cfg_t08_l096_v2, destination cfg_t08_l092_v2 and return XY (71,26).
ROM opcode CC:DA1A has NOT been directly observed as executed PC.
Source world entry was originally cheat-positioned; do not claim
universal story activation. Another ladder tile (22,31) did not
trigger a switch in two locally-cheated up/down gamepad probes, but
absence of a trigger in all story phases is NOT established.
Graph: 149 maps, 60 bound edges, 1297 candidates. See
docs/analysis/pack95_reverse_stair_and_second_ladder_20261011.md.


## 37 verified gamepad entrances and 25 on-screen place names

ROM world hotspot probes tested 40 entries using a disclosed analysis
coordinate cheat to reach the adjacent world cell, followed by a real
SNES Up controller step onto the source trigger. 37 destination pack
switches matched the ROM catalog; 36 distinct packs and 32 configs.
Twenty-five exact config+pack-specific Japanese location names are
proven by local screenshot hashes; 23 were newly attached here.
Five formerly unknown destination coordinates were filled on existing
candidates, including cave pack0x96 at (39,17).
There are still 149 maps, 60 edges, 1297 candidates. Three failed
local trials are NOT general proof of no trigger. No natural world
path, all-story-state access, exact opcode execution PC or Hien
casting was established.

Full table and scope:
docs/analysis/world_37_entries_25_visible_places_20261011.md


## 14 additional live reverse scene exits to the saved world (2026-10-11)

Twenty real SNES Down gamepad return probes from saved world-entered
scene arrivals yielded 14 confirmed scene-pack-to-world-pack switches
to world pack0x4C. The world XY values come from each original
saved-origin context and may not generalize across saves.
No WRAM coordinates were edited during scene reverse input.
Six other locations did not change packs in the local Down72+neutral120
trial, which does NOT rule out alternate exits or flags.
Fourteen context-specific runtime transitions were added, giving
149 map configs, 74 bound edges and 1311 candidates. VM CPU PC,
normal world walking access and all story flags remain unproven.
See docs/analysis/world_scene_14_reverse_exits_20261011.md.


## Pack0x96 scripted/forced downward motion, independent of Up/Down input

Six scene packs whose initial Down72+neutral test never exited were
replayed again with actual SNES Up72+neutral, each source protected.
All six remained on the same pack in the tested current state.
This is NOT universal proof that they lack a return route.

For cave pack0x96 at (39,17), the opposite Up and Down button inputs
produced the exact same 204-frame pack/X/Y trace. Seven steps moved
Y=17 to Y=24 at 9-frame intervals. The native script or physics
mechanism and CPU handler PC are not yet identified.
Six scene+pack scoped directional observations are attached to
map metadata, with an extra 204-frame consistency proof on cfg_t09_l098_v2.
Graph unchanged at 149 maps, 74 bound edges, 1311 candidates.
See docs/analysis/pack96_opposing_direction_forced_motion_and_six_up_probes_20261011.md.


## Pack0x96 title-modal dismissal and world return (2026-10-11)

The same saved cave arrival pack0x96 (39,17) was replayed with genuine
SNES Down, Up, Left, Right and no-button controls. All five 204-frame
pack/XY series matched exactly and automatically descended to (39,24).
An in-game title modal reads 音無しの洞窟, also the name of a distinct
pack0x98 scene. Neutral72+Right72 could not move the player while the
modal remained, but actual A8+neutral64+Right72 moved to (42,24).
After A dismissal, real Up movement from pack0x96 yielded world
pack0x4C switch at frame663807; (39,7) was only temporary post-switch
XY, while (50,129) at frame663897 was stable through frame664216.
One context-specific return edge was added: 149 maps, 75 edges, 1312
candidate transitions; the new exact-pack0x96 onscreen title brings
the attached scene-pack label contexts to 26. All-world walkability,
other saves/story states and exact CPU PC remain unknown.
docs/analysis/pack96_fiveway_modal_escape_world_return_20261011.md


## Five more scene controls and pack0x82 verified saved-world return

Five real scene arrivals (0xBD,0xB9,0xAB,0x82,0x60) were tested with
SNES A8, neutral64, then separate Down/Up/Left/Right96 real controller
inputs (20 total). BD/B9/AB walked around in their local scenes without
exiting this limited window. 82/60 remained stationary from only one
A. Separate 12 sequential A8+neutral20 actions progressed scene
displays. After those twelve A presses, pack82 (40,59) returned with
actual Down96 to world0x4C saved-origin coordinate (175,189),
remaining stable for an extra 360 frames. Pack60 (37,56) remained
unresolved. One contextual real return edge is added, with all
original-world-entry cheat and story/CPU ambiguity preserved:
149 maps, 76 bound edges, 1313 transitions, 26 exact-pack titles.
See docs/analysis/five_scene_A_pack82_return_20261011.md.


## Pack0x60 phase-dependent village appearance and verified world return

Earlier real controller inputs could not move the village player at (37,56)
because a long NPC/event dialogue was still underway after 12 A presses.
An additional 24 A8+neutral20 frames per press (36 total) replayed the
black cutscene and altered village from pink blossom trees to brown
withered vegetation. Afterward, actual Down96 returned from pack0x60
to world0x4C XY(59,155), stable for 360 further neutral frames.
This is one protected saved-world-context proof, not an all-story-gates
assertion; its initial world entrance was cheat-positioned. Exact
minimum press count, executable CPU handler PC, and other saves unknown.
One real return edge and pack+config-scoped visual event proof added.
149 maps, 77 edges, 1314 candidates; 26 exact pack-scoped named scenes.
Full audit: docs/analysis/pack60_dialogue_phase_world_return_20261011.md.
