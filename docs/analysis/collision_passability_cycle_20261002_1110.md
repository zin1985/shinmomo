# Collision / passability rolling cycle (2026-10-02 11:10 JST)

## Baseline refresh

Current main was re-read through `30d02aaf18b58b36cf1cff581ae8344ebef072fd`. Existing primary/secondary map reconstruction, canonical configurations, structural world, transition extraction, runtime object observations, and viewer work remain upstream dependencies and were not reimplemented.

Two newer parallel results materially change the boundary around this work:

- `8bfec6cd0dba26687a5278ad9d2401822c6c0c90` closes opcode59 field0719 bit7 as `obj_palette_cache_half_selector`; the old bit7-unresolved item is therefore merged/completed and must not return to the rolling queue.
- `30d02aaf18b58b36cf1cff581ae8344ebef072fd` adds verified bounded WRAM writes plus a local-only analysis-savestate patcher. This is directly useful for controlled movement/collision experiments once the canonical ROM is visible again.

## Canonical ROM availability

Required ROM: `Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

This cycle attempted to locate the file from the Mole Remote Windows environment. The configured Drive filesystem did not expose it (`ROM_NOT_FOUND`). No substitute ROM was used. Therefore no new ROM-backed collision address, table format, or movement semantic is promoted in this cycle.

Required input for the next ROM-backed step: expose the specified canonical Drive ROM to the Mole Remote/BizHawk environment, then verify size and SHA-256 before execution.

## Collision frontier result

Repository search still exposes no canonical collision/passability model or event-trigger-region format. The L0 frontier remains movement accept/reject path identification, but the experimental method can now be made more deterministic using the newly committed bounded `write-memory` command and save/load-state support:

1. hash-verify the canonical ROM;
2. load one stable field savestate and preserve it as the control;
3. capture candidate position/movement state immediately before a walkable move and a blocked move;
4. use atomic gamepad capture to isolate one directional input;
5. compare only bounded WRAM metadata and control-flow evidence;
6. once candidate coordinate/state fields are independently verified, use bounded write-memory perturbations to distinguish coordinate validation from object occupancy and event/transition gates;
7. commit only derived addresses, classifications, and metadata, never savestates or raw memory/VRAM/OAM/CGRAM dumps.

### Confirmed

- The canonical collision/passability schema is still absent from current main.
- The ROM was not accessible in this cycle, so no replacement ROM was used and no new ROM semantic claim is made.
- opcode59 bit7 is no longer an unresolved rolling item; it is structurally closed as an OBJ palette-cache half selector by the parallel dialogue/controller work.
- Current remote-lab tooling now supports verified bounded memory writes and local-only analysis savestates, reducing the cost of future controlled collision experiments.

### Strong hypothesis

A paired walkable/blocked experiment on one canonical map configuration should isolate the movement discriminator faster than blind ROM scanning, especially now that the same savestate can be restored and bounded state bytes can be perturbed reproducibly.

### Unconfirmed

- collision/passability reader address and record format;
- tile/metatile attribute vs region-grid vs object-occupancy composition;
- event-trigger-region format;
- exact map-world coordinate normalization shared by movement, transitions, and visible objects.

## Rolling priority

1. collision/passability movement accept/reject path using a same-savestate walkable/blocked control pair;
2. map/config -> collision-data crosslink and metadata-only exporter;
3. event-trigger-region reader/record format;
4. transition -> event/trigger crosslink expansion;
5. visible-object coordinate -> map-world coordinate conversion;
6. NPC/sprite/event/dialogue integrated object catalog;
7. native `$0305` writer classification;
8. rebuild-spec integration.

Completed/merged: opcode59 field0719 bit7 consumer closure, because `8bfec6cd` established `obj_palette_cache_half_selector`.

## Progress policy

This cycle improves the experimental capability and removes one stale unresolved dependency, but does not complete a new collision semantic layer. Do not raise the overall project percentage from this cycle alone. The machine-readable project tracker is still stale relative to the parallel map/dialogue/sprite results and needs a dedicated reconciliation against the current G1..G5 evidence before changing the formal overall percentage.
