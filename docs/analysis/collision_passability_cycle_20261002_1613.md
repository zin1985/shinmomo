# Collision / passability rolling cycle — 2026-10-02 16:13 JST

## Baseline checked
- main HEAD at cycle start: `afe3a2d7b1c70bf54bc1e1e63da378863763716c`.
- Rechecked recent commits, `docs/handoff/CURRENT.md`, `progress/project_progress.json`, latest collision notes, and recent map-related history.
- No newer commit exists after the 15:14 evidence-gate note. Existing primary/secondary map reconstruction, structural-world, transition baseline, runtime object observations, and viewer work remain upstream and are not reimplemented.
- Canonical tracker remains dated 2026-09-27 and is stale relative to current parallel evidence.

## Highest-value unresolved boundary
Keep **collision/passability movement accept/reject discriminator** as priority 1. It is still the shortest dependency path from canonical map/configuration data into event-trigger regions, transition/event crosslinks, visible-object world coordinates, and NPC/event/dialogue integration.

## Designated ROM availability
Google Drive search for exact `Shin Momotarou Densetsu (J)_original.smc` returned no accessible result in this run. Therefore the designated ROM could not be used or hash-checked, and no substitute ROM was used.

Required identity remains:
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed.

## Static evidence refinement
### Confirmed
- The current WRAM model treats `$07D9/$0819` as movement-work columns and `$0919/$0959` as a position-like pair in the 64-slot object pool.
- The same-savestate walkable/blocked control-pair design and the 15:14 fail-closed promotion gate remain the canonical next runtime experiment.
- No newer map/collision commit supersedes this boundary.

### Strong hypothesis
The useful discriminator is not a single changing WRAM value but the earliest repeatable control-flow edge where a blocked trial stops before the position-like pair commits while a walkable trial proceeds. `$07D9/$0819` and `$0919/$0959` should be used as temporal anchors for breakpoint placement, not named as collision fields.

### Unconfirmed
- exact movement accept/reject routine and branch
- collision/passability table/layout
- map/config -> passability data crosslink
- ordering/composition of terrain, object occupancy, transition and event-trigger gates
- event-trigger region grammar

## Next runtime protocol
Once the designated ROM is visible and identity-checked:
1. Restore one identical savestate for every trial.
2. Identify the active object slot before input.
3. Capture `$07D9/$0819/$0919/$0959` for that slot before input.
4. Apply exactly one walkable directional input and record the first write/read edges touching the four watch columns.
5. Restore the same savestate, apply exactly one blocked directional input, and record the same edge sequence.
6. Repeat each direction/control at least twice; promote only a stable earliest divergence.
7. Backtrace the stable edge to its first map/config-dependent read. Only then name a terrain/passability source.
8. Use bounded WRAM perturbation only after the field and expected value are independently verified; keep occupancy/event/transition gates separate until controls prove composition.

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
No semantic collision/passability layer closed in this cycle, so formal percent remains unchanged. `progress/project_progress.json` is still the stale 2026-09-27 baseline; percentage reconciliation must be evidence-based and should not be fabricated from the newer parallel work until its top-level goals/tracks are reconciled together.
