# 2026-10-10 native bounds destination overlay for map Viewer

## Result

The prior viewer generated 52 transition edges (3 confirmed, 49 strong
candidates) after exact-address source-hotspot joining.

An existing independent resolver catalog,
`data/maps/transitions/destination_config_bounds_resolution.csv`, contains
110 one-candidate native-bounds resolutions for transitions whose canonical
CSV lacks `destination_config_id`. These are ROM-derived evidence records,
not new runtime confirmations.

The new `tools/python/crosslink_destination_bounds_for_viewer.py` checks each
resolution by unique trigger-address equality, `candidate_count==1`,
destination pack and both arrival coordinates, plus any existing destination
config. No conflicts were found; 110 new destination configuration bindings
were accepted, with no modification to the canonical transition CSV.

The Viewer builder now recomputes both overlays each time:

1. Hotspot source map via exact unique opcode trigger address.
2. Destination map via exact trigger address + unique native bounds proof.

Rebuilt viewer result:
- 149 map configurations;
- 1,295 original transition candidates;
- 1,173 candidates with destination configs (1,063 + 110);
- 54 exact hotspot source bindings;
- **56 navigable source+destination edges** (3 confirmed + 53 strong candidates);
- 1 known source hotspot transition remains phase-dependent (`CC:1160`)
  and is deliberately **not** assigned one destination;
- two native boundary hotspots require context-specific matching because
  both use the same native handler C1:8955.

Each destination overlay carries configuration ID, matched arrival XY, bounds
evidence and provenance in `source_hotspot_binding` /
`destination_bounds_binding` on the viewer transition candidate.

## Deterministic commands

```powershell
py -3 tools/python/crosslink_transition_sources_from_hotspots.py
py -3 tools/python/crosslink_destination_bounds_for_viewer.py
py -3 scripts/test_transition_source_bindings.py
py -3 scripts/test_destination_bounds_overlay.py
py -3 tools/python/build_structural_world_viewer.py
py -3 scripts/ci_validate.py
```

A 6-test synthetic/regression suite verifies conflict rejection, unknown X/Y,
nonunique matching and duplicate native bounds evidence. Previous 8-test
source-joining suite remains intact. No progress percentage increases until
the corresponding formal goal's completion criteria improve.

## Next event-aware graph actions

1. Resolve distinct native-boundary transitions by source/target map state
   rather than applying the global C1:8955 opcode address as a join key.
2. Represent event preconditions and story phase (flags and VM predicates)
   on graph edges, with unknown-state evaluations kept explicit; a
   strong-candidate edge must not masquerade as an unconditional move.
3. Validate overworld -> village -> interior -> overworld with the hidden
   BizHawk lab, comparing exact map, arrival and event state.
4. Continue pack96 and other unresolved entry coordinate work; then complete
   town, world and dungeon floor enumeration, collision and reachability.

ROM files, save states, raw PPU/WRAM captures, and graphics remain outside Git.
