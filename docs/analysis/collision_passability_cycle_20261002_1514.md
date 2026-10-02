# Collision / passability rolling cycle — 2026-10-02 15:14 JST

## Baseline checked
- main HEAD at cycle start: `0752d08d8b0514078130260cd8a35b201bb5ea5e`.
- Rechecked recent commits, `docs/handoff/CURRENT.md`, `progress/project_progress.json`, and the latest collision control-pair note before choosing work.
- No newer map commit exists after the 14:12 collision note; completed map reconstruction / structural-world / transition baseline remains upstream and is not reimplemented.
- The canonical tracker is still dated 2026-09-27 and therefore lags current parallel evidence.

## Highest-value unresolved boundary
Keep **collision/passability movement accept/reject discriminator** as priority 1. It remains the shortest dependency path from canonical map/configuration data into event-trigger regions, transition/event crosslinks, and NPC/world integration.

## ROM availability
The authorized remote environment was probed again for the designated `Shin Momotarou Densetsu (J)_original.smc` under the available `G:\`, `C:\Users\zin\Google Drive`, and `C:\Users\zin\My Drive` roots. No matching file was found. Therefore this cycle did **not** use a ROM and did **not** substitute another ROM.

Required identity remains:
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed.

## Evidence refinement
### Confirmed
- The current WRAM model identifies `$07D9/$0819` as movement-work columns and `$0919/$0959` as a position-like pair in the 64-slot object pool.
- The 14:12 control-pair experiment remains the correct runtime design once the designated ROM becomes visible.
- Current repository code search does not expose an already-canonical collision/passability routine or table under the collision/passability terminology, so no completed implementation is being duplicated.

### Strong hypothesis
A same-savestate walkable-vs-blocked single-input comparison on the active slot should separate at least two stages: movement intent/work (`$07D9/$0819`) and position commit (`$0919/$0959`). The earliest stable divergence is the best breakpoint seed for finding the accept/reject branch.

### Unconfirmed
- exact accept/reject routine and branch
- collision/passability table/layout
- map/config -> passability data crosslink
- composition order of terrain, object occupancy, transition and event-trigger gates
- event-trigger region grammar

## Static fallback completed this cycle
Because runtime ROM evidence is unavailable, the useful fallback is to make the next runtime trace fail-closed:
1. Do not infer collision from position deltas alone; require a reproducible blocked/walkable control pair from the same savestate.
2. Treat `$07D9/$0819` and `$0919/$0959` only as watch columns, not as collision fields.
3. Promote a discriminator only when the same writer/reader edge explains repeated accept/reject outcomes.
4. Require at least one map/config-dependent read before naming a terrain/passability data source.
5. Keep object occupancy and event/transition gating separate until perturbation or control cases prove composition.

## Rolling schedule
1. **collision movement accept/reject discriminator** — active; runtime confirmation blocked on designated ROM visibility.
2. **map/config -> collision/passability data crosslink** — queued after discriminator.
3. **event-trigger region grammar** — queued.
4. **transition -> event/trigger crosslink expansion** — queued; consume newer parallel transition results and do not reset the baseline.
5. **visible-object coordinates -> map-world coordinates** — queued.
6. **NPC/sprite/event/dialogue integration** — queued; consume phase-aware dialogue and current sprite/controller evidence.
7. **native `$0305` writer classification** — queued.
8. **rebuild-spec integration** — queued.

## Progress decision
No semantic collision/passability layer closed in this cycle. Keep formal percent unchanged. The stale 2026-09-27 `progress/project_progress.json` still requires a dedicated reconciliation before percentage changes can safely represent the newer parallel map/dialogue/controller evidence.
