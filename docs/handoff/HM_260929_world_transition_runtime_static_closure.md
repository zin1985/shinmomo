# 2026-09-29 world-map transition runtime/static closure

## Classification

NEW ANALYSIS / cross-track integration based on the latest canonical main evidence.

## Confirmed

- Runtime world-map source is `cfg_t01_l001_v1`, pack `0x4C`, coordinate `(54,236)`.
- At runtime frame 14455, `$0305` changes `0x4C -> 0x50`.
- The unique matching terminal VM transition is `CC:0B08`, script pack `0x4C`, record 2, entry `0x77`, opcode `0x53`.
- Its destination is pack `0x50`, entry `0x02`, canonical config `cfg_t04_l008_v2`.
- The aligned opcode `0x58` setter at `CC:1C4E` predicts destination coordinate `(29,55)`; runtime reaches exactly `(29,55)`.
- The visible destination label is `旅立ちの村`.
- This is the first preserved runtime/static transition closure that proves source config, exact VM trigger, destination config, and arrival coordinate in one chain.

## Strong inference

The transition catalog can now use runtime evidence files as fail-closed promotion fixtures: a row is promoted only when trigger address, source/destination pack, destination entry, and coordinates agree. This is a reusable verification pattern for future map edges.

## Not proven

- Script-pack identity is not a general source-map identity rule.
- The earlier interior `0x2E -> 0x50` runtime edge still lacks its exact event opcode.
- Most of the 1,238 VM transition candidates still lack source configuration.
- Collision/passability and trigger-region semantics are not implied by this transition closure.

## Priority update

1. Capture/promote more source-config + exact-trigger runtime/static transition closures.
2. Resolve the older `0x2E -> 0x50` edge to its exact event opcode.
3. Join transition triggers to event records/conditions.
4. Decode collision/passability and event-trigger regions against canonical configs.
5. Join visible-object coordinates and canonical sprite/entity identities into map-world coordinates.
6. Feed map/event/dialogue/NPC joins into the portable world specification and ROM rebuild gap manifest.
7. Keep Save/SRAM and audio/APU as independent high-value subsystem gaps.

## Progress interpretation

This materially advances G4 event-graph validation and G5 portable verification fixtures. It does not justify treating map rendering or transition catalog coverage as whole-game completion. A conservative top-level proposal remains G1 48, G2 63, G3 49, G4 47, G5 50 (51.4% mean) until the canonical progress tracker is synchronized.
