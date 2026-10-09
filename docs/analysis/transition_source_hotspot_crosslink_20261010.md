# 2026-10-10 exact opcode source-map crosslink and viewer integration

## Goal

Move toward a complete, event-aware world graph (world, villages, interiors,
dungeons and story phases) by linking already-derived evidence rather than
re-extracting ROM material or guessing map identity from script-pack numbers.

## Starting baseline

- 149 viewer map configurations.
- 1,295 transition candidates, 3 previously bound/confirmed viewer edges.
- 57 separately proven VM/native source transition hotspots.
- Project top-goal progress unchanged: 51.4%.

## New reproducible join

Tool: `tools/python/crosslink_transition_sources_from_hotspots.py`

Command: `py -3 tools/python/crosslink_transition_sources_from_hotspots.py`

Outputs:
- `data/maps/transitions/source_hotspot_transition_bindings.csv`
- `data/maps/transitions/source_hotspot_transition_bindings_summary.json`

Method: join on an **exact, unique instruction trigger address** only. Reject
ambiguity, any contradiction in already-present source, destination config,
arrival X/Y or event record, and repeated source bindings. Do not mutate the
canonical transition candidate CSV.

Observed baseline:
- 55/57 source hotspots have unique exact-address matches.
- 1 of those 55 was already bound consistently.
- 54 new source-map candidate bindings, no contradictions.
- 49 newly navigable map edges; 5 new bindings still lack destination config.
- 2 native boundary hotspots intentionally remain unmatched to VM instruction
  address joins: `hotspot_native_tabidachi_south_exit_x28_y55` and
  `hotspot_native_pack2e_south_exit_candidate`. These need native/context
  matching and must **not** be matched by C1:8955 alone because they share it.

`tools/python/build_structural_world_viewer.py` now recomputes this source
overlay in memory during every viewer build, avoiding stale-CSV dependence.
`viewer/data/world.json` reflects 52 edges: 3 previously confirmed plus
49 strong candidate edges, with per-edge hotspot address, source grid
coordinate/shape, confidence, evidence and provenance. Candidate counts remain
1,295; original source rows remain untouched. **No new transition has been
reclassified as runtime-confirmed.**

## Verified checks

- Eight regression tests passed in
  `scripts/test_transition_source_bindings.py`.
- `scripts/ci_validate.py` passed; overall progress remains 51.4%.
- A full viewer rebuild produced 149 maps, 1,295 candidates, 52 edges,
  exactly 3 confirmed, 54 source overlays.

## Next high-value tasks

1. The separate bounds-resolution catalog
   `data/maps/transitions/destination_config_bounds_resolution.csv`
   contains 110 unique, conflict-free exact transition-address/pack/arrival-XY
   config resolutions. Integrate conservatively as a **destination overlay**,
   preserving raw source CSV and confidence. Four of the five newly
   source-bound but destination-unresolved rows are covered; `CC:1160`
   remains phase-dependent and must not be collapsed into a single destination.
2. Native boundary transitions need context/phase-specific identities, not
   global C1:8955 address matching.
3. Join exact source trigger regions to the graph and gate navigation by story
   predicates; currently bound candidate edges are not proof of unconditional
   reachability.
4. Validate a full end-to-end overworld -> village -> interior -> overworld
   traversal using the hidden dedicated BizHawk bridge. Compare screenshots,
   frame state, event branches, NPC placements and return positions.
5. Expand graph to dungeons/floors and automatically enumerate unreachable
   maps, return-path gaps, branches and unverified conditions.

## Safety

- Do not claim all 1,295 transitions are verified/connected.
- Do not equate destination pack with a source map or borrow XY from
  neighboring packs or identical config.
- Do not commit ROM, state, raw captures, or original graphics.
- Worktree/main HEAD should be checked before merging. Preserve parallel
  dialogue, sprite, and transition worktrees and the previous pack96 task.
