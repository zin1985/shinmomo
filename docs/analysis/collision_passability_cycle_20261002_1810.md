# Collision / passability rolling cycle — 2026-10-02 18:10 JST

## Baseline checked
- main HEAD at cycle start: `299f3c70b23d836ccd04553682c8e6291a9180c7`.
- Rechecked recent commits, `docs/handoff/CURRENT.md`, `progress/project_progress.json`, the 17:19 collision evidence schema, and recent map/dialogue/remote-lab history.
- No newer commit supersedes the established primary/secondary map reconstruction, structural-world, transition, runtime-object, or viewer results; they remain upstream and are not reimplemented.
- Canonical tracker remains dated 2026-09-27 and is stale relative to current parallel evidence.

## Highest-value unresolved boundary
Keep **collision/passability movement accept/reject discriminator** as priority 1. It remains the shortest dependency path from canonical map/configuration data into event-trigger regions, transition/event crosslinks, visible-object world coordinates, and NPC/event/dialogue integration.

## Designated ROM availability
Google Drive search for the exact designated filename `Shin Momotarou Densetsu (J)_original.smc` returned no accessible result in this run. Therefore the designated ROM could not be used or hash-checked, and no substitute ROM was used.

Required identity remains:
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed.

## Static refinement: discriminator candidate scoring
Because runtime evidence is still blocked, this cycle adds a fail-closed ranking rule for the next capture so the first divergence is not automatically mislabeled as collision.

For each repeatable walkable/blocked edge divergence, score evidence in this order:
1. **pre-commit timing**: edge occurs before `$0919/$0959` position-like commit;
2. **repeatability**: same edge and branch outcome reproduce in both repeats of each control;
3. **direction sensitivity**: changing only attempted direction changes the relevant input/read while preserving the starting state;
4. **map/config provenance**: an upstream read can be joined to current canonical map/config data;
5. **gate isolation**: object occupancy, event trigger, and transition side effects are absent or separately controlled.

A candidate may be called `movement_accept_reject_discriminator` after 1–2 are satisfied under the existing promotion gate. It may be called `terrain/passability` only after 4 is satisfied. Criterion 5 determines whether the result is terrain-only or a composite movement gate.

### Confirmed
- `$07D9/$0819` remain movement-work columns and `$0919/$0959` a position-like pair in the current 64-slot object-pool model.
- The four columns are temporal anchors, not collision fields.
- Current repository evidence does not yet justify a canonical collision table/routine address.

### Strong hypothesis
The first useful discriminator will be a repeatable pre-position-commit control-flow divergence. Ranking candidates by map/config provenance should distinguish terrain/passability from occupancy/event/transition gates with fewer perturbation trials.

### Unconfirmed
- exact movement accept/reject routine and branch
- collision/passability table/layout
- map/config -> passability data crosslink
- terrain/object/event/transition gate composition and order
- event-trigger region grammar

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
No semantic collision/passability layer closed in this cycle, so formal percent remains unchanged. `progress/project_progress.json` remains the stale 2026-09-27 baseline. This cycle sharpens evidence ranking but does not justify a percentage increase.
