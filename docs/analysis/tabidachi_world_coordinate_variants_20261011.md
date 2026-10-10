# Tabidachi village/world coordinate-sensitive native returns
2026-10-11. Canonical repo: zin1985/shinmomo.

## Confirmed runtime pairs

A playable save was loaded with the hidden isolated BizHawk laboratory,
then source positions were observed by one-frame SNES controller captures.

| Village source cell | Return world cell | Runtime evidence |
| --- | --- | --- |
| (28,55) | (54,237) | prior verified boundary replay 2026-09-30 |
| **(29,55)** | **(55,237)** | newly verified 2026-10-11 exact one-frame replay |

The second pairing is now an *independent* reproduced exit, not a
generalization from the first. Both x28 and x29 have been observed,
but the full exit width and any formula for other x positions are
NOT proven.

### Village to world, newly tested x29

Starting protected village state: pack 0x50, x29,y54,
frame 662166. Run exactly one Down frame per isolated command.

- Frame 662169: x29,y55, within the village's southern bounds
- Frame 662177: x29,y56, first observed out-of-bounds
- Frame **662186**: current pack changes 0x50 -> 0x4C,
  world coordinates become (55,237)
- Twenty consecutive one-frame captures, no gaps or desktop input

Mechanism is the native out-of-bounds saved-map-state return, NOT
the normal VM opcode 0x56. Local evidence:
native_50_to4c_x29_perframe_20261011.json and individual local
vmtrace_*.json snapshots.

### World to village, tested x55

Starting protected world state: pack 0x4C, x55,y236,
frame 663046. Move Down one frame at a time.

- Frame 663048: x55,y237, the known world->village hotspot
- Frame **663064**: pack 0x4C -> pack 0x50
- Frame 663224, after transition settles: village (29,55)
- Eighteen exact input-frame captures, plus independently rerun
  post-transition destination/coordinate check

The world hotspot is statically associated with event script CC:0B08,
a normal VM 0x53 wrapper. The CPU execution hook did NOT produce an
event, so **the VM handler execution address itself is not proven**.
WRAM frame and arrival evidence is independently real.

## Viewer behavior

The native cfg_t04_l008_v2 -> cfg_t01_l001_v1 edge already exists as
catalog_transition_1294. It still has one representative arrival
(54,237) and unchanged confirmed confidence. The new provenance
is attached as two EXACT source-coordinate/arrival variants:

- (28,55) -> (54,237)
- (29,55) -> (55,237)

The viewer shows both pairs. When an inspected source coordinate is
known and matches one exact pair, it focuses the appropriate world
arrival. When no exact source coordinate is selected, the Viewer
opens the destination map without pretending a specific arrival
coordinate. No new graph edge or reachability predicate was invented.

The previous native saved return position-rectangle x=54..55,y237
contains both observed world arrivals. This does not prove that all
rectangle points or all village exit cells are traversable. The
viewer still marks navigable_now=false / activation unknown unless
active game state and saved return context are known.

## Reproducible tools

- tools/python/verify_tabidachi_world_roundtrip.py reads the three
  local-only capture manifests and all their individual one-frame
  input logs, requiring contiguous frames, valid no-desktop-input
  identity, valid pack switches and exact post-settle arrival.
- data/maps/transitions/tabidachi_x29_world_x55_roundtrip_20261011.json
  contains derived metadata and raw local capture SHA-256 digests.
- scripts/test_tabidachi_world_roundtrip.py has synthetic negative
  tests for forged input, wrong coordinates, missing frames, etc.
- tools/python/build_native_saved_return_context.py includes a
  fail-closed contextual native coordinate variant attach helper.
- tools/python/build_structural_world_viewer.py applies the proof
  only to the existing unique native reverse edge.
- scripts/test_native_saved_return_context.py protects both
  source variants, no extrapolation, and non-executable story gating.
- viewer/viewer.js renders both exact pairs and avoids a guessed
  coordinate when selecting the destination map.

Raw screenshots, emulator states, SaveRAM and individual trace files
are never committed to Git.

## Future expansion

Reproduce other x cells, if any, rather than extrapolating an affine
mapping from two observations. For each native boundary and scripted
transition, capture source cell, first crossing frame, initial pack
switch, post-settle arrival and saved return-stack context.
Investigate the BizHawk execution-hook backend separately:
34 hooks registered but 0 handler/write hits even during proven
native map transitions. The reliable evidence here is frame-exact
WRAM state history, NOT a CPU opcode trace.

Project overall completion remains 51.4%, with 149 map configs and
56 existing bound edges; this change improves arrival precision.
