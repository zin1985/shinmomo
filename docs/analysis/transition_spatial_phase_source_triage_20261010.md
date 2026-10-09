# Event-aware transition spatial gates, phase alternatives, and source-owner triage
2026-10-10 continuation, canonical repository: zin1985/shinmomo

## What was changed

The structural Viewer now includes research-only **spatial conditions** for the
54 VM transition candidates with independently linked source hotspots. Each
condition contains map config, inclusive source grid bounds, hotspot identity
and provenance. The invariant is important:

- Known **outside** a confirmed VM hotspot rectangle: this inspected
  coordinate cannot activate that particular transition.
- Known **inside** a confirmed VM hotspot rectangle: the coordinate clause
  matches, but story flags, event VM branching, and runtime state remain unknown.
- No inspected coordinate or a native boundary candidate: unknown. Even if
  one native exit cell is observed, the full passable boundary might be wider;
  do not reject other cells as impossible.

This is a three-valued research predicate, **not** game execution. The
Viewer-selected focus is a document inspection position, NOT the emulator's
current WRAM player coordinate. No transition has been upgraded to
`navigable_now`.

## Phase-dependent destination (CC:1160)

The existing ROM-backed evidence for transition CC:1160 is retained as a
**destination set** of five configurations:
- cfg_t04_l085_v2
- cfg_t04_l086_v2
- cfg_t05_l087_v2
- cfg_t04_l088_v2
- cfg_t04_l089_v2

Source config is cfg_t01_l001_v1 at (238,173), destination pack 0xCE entry
0x02, arrival (22,28). Destination-side branch / phase flag still unknown.
This transition remains outside `transition_edges` because no unique destination
can be chosen. The Viewer displays all five variants as an unresolved group,
without pretending any is currently reachable.

Existing 149 maps, 1,295 candidates, 56 bound edges, and 3 runtime-confirmed
edges remain unchanged. Official top-goal progress stays 51.4%.

## Reproducible source-owner triage

Run `py -3 tools/python/triage_unbound_transition_sources.py`.

The resulting
`data/maps/transitions/source_unbound_investigation_queue.json` classifies the
1,238 source-unbound derived candidates by VM opcode family and script pack:

- 721 `vm_opcode_0x56_terminal`
- 338 `vm_opcode_0x53_transition_wrapper_terminal`
- 93 `vm_opcode_0x53_nonterminal_shape`
- 86 remaining other forms
- 1,028 transitions whose script pack currently has exactly one known
  map-config context, 209 whose script pack has multiple, and one with none.

The 1,028 **are only investigative leads**, NOT new source bindings.
A script pack can be called while a different map is active. A unique
crosslink is not sufficient: decode owner/event call-site, active pack,
saved-map-stack context and scene state before promoting any source config.

The raw canonical CSV has more source-null rows than the generated Viewer
because the Viewer already integrates source-hotspot overlays.

## Implementation, commands and testing

- `tools/python/transition_gate_predicates.py`: pure spatial- and phase-condition
  metadata plus conservative research-coordinate evaluation.
- `tools/python/triage_unbound_transition_sources.py`: source-ownership
  investigation queue, no mutations of candidate CSV.
- `scripts/test_transition_spatial_phase_gates.py`: regression tests on
  known inside/outside/unknown paths, native non-exclusive boundaries,
  phase set identity, and no inferred source config.
- `tools/python/build_structural_world_viewer.py`: additional condition and
  phase metadata during each deterministic build.
- `viewer/viewer.js`: displays a research-coordinate clue and the unresolved
  five-map family, still preview-only.

Commands:

```powershell
py -3 tools/python/build_structural_world_viewer.py
py -3 tools/python/triage_unbound_transition_sources.py
py -3 scripts/test_transition_spatial_phase_gates.py
py -3 scripts/ci_validate.py
node --check viewer/viewer.js
```

## Next evidence goal

1. Work on the dominant VM opcode 0x56 source-ownership problem. Investigate
   specific event record and caller contexts for high-frequency script packs
   rather than assuming script-pack identity equals current map.
2. Verify a full world -> village -> interior -> village -> world traversal
   using the isolated hidden BizHawk lab and exact before/after WRAM.
3. Recover the pack-0xCE phase discriminator at CD:9140..91DC and prove
   which configuration(s) are reachable for CC:1160.
4. Upgrade a gate to true only after verified control-flow, flag state, active
   scene context, and movement prerequisites, keeping native return-stack
   dependencies explicit.
5. Repeat this method for all villages and dungeon floors and track graph
   coverage without inventing extra edges.
