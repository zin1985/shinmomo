# Collision / passability rolling cycle (2026-10-02 12:10 JST)

## Baseline refresh

Current main was refreshed through `d53b11f8f5989b20345f8185db1db5df77f9f17f`. Parallel work after the previous collision cycle added a phase-aware Tabidachi dialogue archive; existing map reconstruction, structural world, transition extraction, runtime object observations, and viewer outputs remain upstream and were not reimplemented.

The machine-readable project tracker is still dated 2026-09-27 and therefore remains stale relative to current map/dialogue/sprite/controller evidence.

## Canonical ROM availability

Required ROM: `Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

Mole Remote health succeeded in this cycle, but the combined coordination/Drive filesystem probe failed before producing a canonical-ROM path/hash result. Therefore this cycle did not use a ROM, and no substitute ROM was used. No new ROM-backed collision address, table layout, or movement semantic is promoted.

Required input remains an accessible canonical Drive ROM path in the Mole Remote/BizHawk environment, followed by size/SHA-256 verification.

## Priority decision

Collision/passability remains the highest-information unresolved boundary because it can join canonical map configuration, runtime coordinates, transitions, event-trigger regions, and later NPC/event/dialogue integration. The new phase-aware dialogue archive is useful downstream but does not supersede this dependency.

### Confirmed

- current main advanced to `d53b11f8f5989b20345f8185db1db5df77f9f17f`;
- the formal project tracker is still stale at 2026-09-27;
- Mole Remote itself answered health successfully;
- the canonical ROM could not be verified or used in this cycle;
- no substitute ROM was used;
- no canonical collision/passability schema has yet been promoted by this workstream.

### Strong hypothesis

Once the canonical ROM is visible, a same-savestate walkable/blocked atomic-input pair remains the shortest route to the movement discriminator. Bounded WRAM capture/write support should then distinguish coordinate validation from object occupancy and event/transition gates.

### Unconfirmed

- collision/passability reader address and record format;
- tile/metatile attribute vs region-grid vs object-occupancy composition;
- event-trigger-region record format;
- shared map-world coordinate normalization.

## Rolling priority

1. collision/passability movement accept/reject path using a same-savestate walkable/blocked control pair;
2. map/config -> collision-data crosslink and metadata-only exporter;
3. event-trigger-region reader/record format;
4. transition -> event/trigger crosslink expansion;
5. visible-object coordinate -> map-world coordinate conversion;
6. NPC/sprite/event/dialogue integrated object catalog, consuming the new phase-aware dialogue archive;
7. native `$0305` writer classification;
8. rebuild-spec integration.

## Progress policy

No collision semantic layer was closed in this cycle. Keep formal overall progress unchanged until the stale tracker is reconciled or ROM-backed collision evidence closes a new layer.
