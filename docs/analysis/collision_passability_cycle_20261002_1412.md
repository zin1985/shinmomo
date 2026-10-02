# Collision / passability rolling cycle — 2026-10-02 14:12 JST

## Baseline checked
- main HEAD at cycle start: `a069471350e840340bf47c663eb516a06efa3b13`
- Rechecked recent commits and `progress/project_progress.json` before choosing work.
- Existing primary/secondary map reconstruction, Mode1/Mode7 composition, canonical map configuration, structural world, runtime object observation and transition extraction are treated as upstream completed work and are not reimplemented here.
- Tracker is still the 2026-09-27 baseline and therefore lags current map/dialogue/controller evidence.

## Highest-value unresolved boundary
Collision/passability remains the highest-value frontier because it can connect canonical map/configuration data to movement acceptance, event-trigger regions and transition/event crosslinks.

## ROM availability
The designated ROM `Shin Momotarou Densetsu (J)_original.smc` was searched from the authorized remote environment under the available Google Drive candidate roots and was not found (`ROM_NOT_FOUND`). Therefore this cycle did **not** use a ROM and did **not** substitute another ROM. Required ROM identity remains:
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed.

## Evidence boundary
### Confirmed
- Existing WRAM model identifies a 64-slot SoA object pool in `$0619..$0A18`.
- Current tracker evidence classifies `$07D9/$0819` as movement-work columns and `$0919/$0959` as a position-like pair.
- The current remote-lab tooling can support bounded, verified WRAM perturbation once a valid local analysis savestate and the designated ROM are available.

### Strong hypothesis
For an active player/object slot, a same-savestate walkable-vs-blocked one-input comparison focused first on `$07D9/$0819/$0919/$0959` should expose a movement accept/reject boundary with substantially less noise than a whole-WRAM diff. A blocked attempt is expected to diverge in movement-work state while suppressing or altering the position commit.

### Unconfirmed
- exact collision/passability routine
- collision table/layout and map/config crosslink
- whether terrain, object occupancy and event-trigger gates share one discriminator or compose multiple gates
- event-trigger region record format

## Next experiment
1. Resolve the designated Drive ROM and verify size/SHA-256 before execution.
2. Start from one local-only savestate with an adjacent walkable tile and blocked tile.
3. Identify the active player/object slot without changing game state.
4. Capture `$07D9/$0819/$0919/$0959` for that slot before/after exactly one directional input in each control case.
5. If a stable accept/reject delta appears, trace the first writer/reader responsible for the divergent field.
6. Crosslink that routine's map/config-dependent reads to canonical map configuration.
7. Only after a reproducible discriminator exists, use bounded WRAM perturbation to separate terrain collision from object/event gating.

## Rolling schedule
1. **collision movement accept/reject discriminator** — active; blocked on designated ROM visibility for runtime confirmation.
2. **map/config -> collision/passability data crosslink** — queued after discriminator.
3. **event-trigger region grammar** — queued.
4. **transition -> event/trigger crosslink expansion** — queued; preserve newer parallel transition results.
5. **visible-object coordinates -> map-world coordinates** — queued.
6. **NPC/sprite/event/dialogue integration** — queued; consume phase-aware dialogue and current sprite evidence.
7. **native `$0305` writer classification** — queued.
8. **rebuild-spec integration** — queued.

## Progress decision
No semantic collision layer was closed in this cycle, so no percentage increase is justified. Keep the formal project percentage unchanged until evidence-backed collision/passability semantics land. The stale 2026-09-27 tracker still needs a separate reconciliation with newer parallel results.
