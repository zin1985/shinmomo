# Collision / passability rolling cycle — 2026-10-02 17:19 JST

## Baseline checked
- main HEAD at cycle start: `69b80fee8bbd765399367a845498e7efc1fe7dc8`.
- Rechecked recent commits, `progress/project_progress.json`, the 16:13 collision note, and recent map/dialogue/remote-lab history.
- No newer commit supersedes the established primary/secondary map reconstruction, structural-world, transition, runtime-object, or viewer results; they are treated as upstream and are not reimplemented.
- Canonical tracker remains dated 2026-09-27 and is stale relative to current parallel evidence.

## Highest-value unresolved boundary
Keep **collision/passability movement accept/reject discriminator** as priority 1. This remains the shortest dependency path from canonical map/configuration data into event-trigger regions, transition/event crosslinks, visible-object world coordinates, and NPC/event/dialogue integration.

## Designated ROM availability
Google Drive search for `Shin Momotarou Densetsu (J)_original.smc` / `Shin Momotarou Densetsu original` returned no accessible result in this run. Therefore the designated ROM could not be used or hash-checked, and no substitute ROM was used.

Required identity remains:
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed.

## Static refinement: minimal runtime evidence schema
Because the ROM remains unavailable, this cycle avoids inventing routine/table addresses and instead fixes the minimum evidence record needed to make the next runtime experiment machine-comparable rather than narrative-only.

For each trial, record at minimum:
- `savestate_id` / reproducible starting-state fingerprint
- `active_slot`
- `direction`
- `expected_control`: `walkable` or `blocked`
- pre-input values for `$07D9/$0819/$0919/$0959` at the active slot
- ordered first-touch edges for those four columns: CPU address, read/write, before/after value
- whether the position-like pair committed
- earliest stable divergence edge versus the paired control
- first upstream map/config-dependent read if reached
- repeat index and whether the edge sequence reproduced

### Confirmed
- `$07D9/$0819` remain movement-work columns and `$0919/$0959` a position-like pair in the current 64-slot object-pool model.
- A single WRAM value change is insufficient evidence for collision semantics.
- Promotion requires a same-savestate walkable/blocked control pair with repeatable edge-sequence divergence.

### Strong hypothesis
The useful discriminator will be the earliest repeatable control-flow edge that separates blocked trials from trials that proceed to the position-like commit. The four known columns are temporal anchors, not collision fields.

### Unconfirmed
- exact movement accept/reject routine and branch
- collision/passability table/layout
- map/config -> passability data crosslink
- terrain/object/event/transition gate composition and order
- event-trigger region grammar

## Promotion gate
Promote a candidate edge to `movement_accept_reject_discriminator` only when:
1. identical starting state is demonstrated,
2. both walkable and blocked controls reproduce at least twice,
3. the same earliest edge divergence explains the control pair,
4. the divergence occurs before/at the position-like commit boundary rather than after movement has already resolved.

Promote further to `terrain/passability` only after at least one upstream read is tied to current map/config-derived data. Object occupancy, transition, and event-trigger gating remain separate until controlled evidence joins them.

## Rolling schedule
1. **collision movement accept/reject discriminator** — active; runtime confirmation blocked on designated ROM visibility.
2. **map/config -> collision/passability data crosslink** — queued after discriminator.
3. **event-trigger region grammar** — queued.
4. **transition -> event/trigger crosslink expansion** — queued; consume newer parallel transition results and never reset the established baseline.
5. **visible-object coordinates -> map-world coordinates** — queued.
6. **NPC/sprite/event/dialogue integration** — queued; consume phase-aware dialogue and current sprite/controller evidence.
7. **native `$0305` writer classification** — queued.
8. **rebuild-spec integration** — queued.

## Progress decision
No semantic collision/passability layer closed in this cycle, so formal percent remains unchanged. `progress/project_progress.json` is still the stale 2026-09-27 baseline. This cycle improves reproducibility and evidence quality but does not justify a percentage increase.
