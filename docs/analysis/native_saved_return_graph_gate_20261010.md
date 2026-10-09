# Shinmomo event-aware world graph: native return contexts and activation-gate frontier (2026-10-10)

## Verified input and implementation

Project: `zin1985/shinmomo`. ROM identity is unchanged; no ROM/raw
screens/state files have been committed. Existing state: 149 Viewer map
configurations, 1,295 transition candidates, 56 candidate/confirmed map
edges, including 3 runtime-confirmed. The top-goal score stays 51.4%.

The apparent native C1:8955 reuse is **one shared handler**, not one fixed
transition. Two already-bound runtime edges were joined by the ordered pair
of source map and destination map and then cross-checked against a unique
saved-return origin from
`data/maps/transitions/source_saved_return_origins.csv`. Matching only
C1:8955 is forbidden.

| Source -> destination | Existing edge | Native source proof | Saved return arrival |
| --- | --- | --- | --- |
| cfg_t04_l008_v2 -> cfg_t01_l001_v1 | catalog_transition_1294 | Exact cell (28,55) confirmed at runtime; south exit | (54,237), runtime-backed |
| cfg_t07_l015_v2 -> cfg_t04_l008_v2 | catalog_transition_0000 | Candidate corridor X=8..10, Y=12; reverse travel observed, individual X cells unverified | (29,17), saved-state origin evidence |

The return X/Y is derived from the independent saved-return origin and
only attached when the coordinate falls inside that source rectangle.
There were two successful, unique joins and no conflicts. **No new edge
was added**, and neither original confidence nor full corridor passability
was promoted.

Tool: `tools/python/build_native_saved_return_context.py`
with regression tests in `scripts/test_native_saved_return_context.py`.

## Conservative event-state semantics

Each of the 1,295 Viewer transition candidates now carries an explicit
`activation_gate` record. Its possible evaluation is currently
`unknown`: an observed transition happened in at least one runtime
state but does NOT prove it is available in every story phase or player
position. Context-sensitive native exits require all three conditions:
player at an applicable source exit, an actual out-of-bounds movement,
and a compatible saved-map return stack. VM transitions with a source
hotspot require being in the region **and** the VM control-flow/story
predicate; latter is not yet decoded for all cases.

Viewer edge cards show "condition not established" and label the
button `inspect map`. It only opens the destination map for research;
it does not claim the current game state can travel there. Exact
runtime/flag predicate evaluation is a subsequent task.

World data schema advances to 9 and contains
`native_boundary_context_summary`, preserved provenance,
context-specific source regions, saved return rectangles and arrival XY.

## Whole-world topology audit

Run:

```powershell
py -3 tools/python/build_structural_world_viewer.py
py -3 tools/python/audit_world_graph_coverage.py
py -3 scripts/test_native_saved_return_context.py
py -3 scripts/test_world_graph_coverage.py
```

The graph is **incomplete**. With 149 maps and 56 bound edges:

- Only 3 maps have any outgoing bound transition. 146 lack a connected outgoing
  transition (this is missing *catalog binding*, not evidence of in-game isolation).
- 50 maps have at least one incoming bound transition.
- There are 100 weakly connected components, largest size 50 maps.
- 47 map pairs have no opposite-direction bound edge. These are leads
  for investigation, not necessarily errors: some story events are
  legitimately one-way or return via different locations.
- 1,238 transition candidates remain source-unbound; 122 remain
  destination-unbound.
- All 56 viewer bound edges have `activation_gate.evaluation=unknown`
  until story-state and movement prerequisites are proven.

Audit artifacts:
`tools/python/audit_world_graph_coverage.py`,
`data/maps/transitions/world_graph_coverage_summary.json` and
`scripts/test_world_graph_coverage.py`.

## Next evidence-oriented steps

1. Acquire a deterministic runtime sample of interior->village boundary
   including the exact pre-exit X and collision test for X=8..10.
   Use the dedicated hidden BizHawk lab; do not interfere with main desktop
   input. Keep savestates and screenshots local-only.
2. Decode the specific VM branch predicates guarding the high-confidence
   source hotspots. Implement real tri-state predicate evaluation from
   verified operands/flags only, not English condition text.
3. Expand source identity beyond the 57 manually linked hotspots by
   tracing pack contexts, event-record ownership, and native route stack.
   Begin with the 1,238 currently source-unbound candidates.
4. Validate a world->village->interior->world round trip with exact
   before/after WRAM and screenshot evidence for all four directions/edges.
5. Continue pack96/entry02 source work and dungeon/floor reachability.

**Do not increase the official project completion percentage** just because
more provenance fields or unknown-state gates were attached.
