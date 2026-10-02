# Collision / passability rolling cycle (2026-10-02 10:17 JST)

## Baseline recheck

- main HEAD at commit boundary: `1f1361c740f1813114d0f1abc1497fbb0a1009d1`.
- Rechecked `docs/handoff/CURRENT.md`, `progress/current_task.json`, `progress/project_progress.json`, recent commits, and the collision frontier note.
- Parallel work after the frontier commit includes sprite coverage being surfaced into the project-progress viewer (`4b745bd...`), opcode59 field06D9 direction-reader confirmation (`fb7989d...`), and family50 text-token closure (`1f1361c...`). These are upstream gains and are not reimplemented here.
- The machine-readable project tracker remains stale at `updated_at=2026-09-27`; this cycle does not fabricate a new overall percentage from local subsystem closure.

## Selected theme

Continue the highest-information unresolved boundary: **collision/passability movement-decision path identification**, with event-trigger-region reconstruction queued behind it. Existing primary/secondary map reconstruction, canonical configurations, structural world, transition extraction, renderer work, and runtime logical/visible-object observations are treated as completed upstream dependencies.

## Canonical ROM availability

Required ROM: `Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

Two independent access attempts failed this cycle:

1. Google Drive connector search returned no accessible file with the canonical ROM filename.
2. Mole Remote could not execute because its MCP tunnel reported `mcp_initialization_required` before operational requests.

**Drive指定ROMへアクセスできなかった. No substitute ROM was used.** Therefore no ROM-backed collision address/table/semantic claim is promoted in this cycle.

## Repository-backed result

A current-main code search for dedicated collision/passability/movement discriminator artifacts still returned no canonical implementation/model. This strengthens the frontier definition but is not evidence for any particular storage format.

### Confirmed

- Collision/passability remains an unresolved subsystem boundary on current main.
- Existing canonical map/configuration and transition products are the correct join keys once a movement discriminator is found.
- The current blocker is canonical-ROM runtime/static access, not missing map reconstruction.

### Strong hypotheses retained for testing

- The movement accept/reject path will consume either tile/metatile attributes, configuration-specific auxiliary data, object occupancy, region data, or a composite of these.
- Event-trigger regions may reuse coordinate normalization with movement/transition checks, but must remain separate until a shared reader is demonstrated.

### Unconfirmed

- collision table address/format;
- player/NPC movement collision routine;
- collision coordinate transform;
- event-trigger-region format;
- whether transitions are a generic trigger-region subtype.

## Rolling schedule

1. **collision/passability movement-decision path**: canonical ROM hash check, then bounded walkable-vs-blocked movement trace.
2. **map/config -> collision-data crosslink**: classify map-dependent reads and export metadata only.
3. **event-trigger-region reader/record format**: bounded activation trace after static movement discriminator exists.
4. **transition -> event/trigger crosslink expansion**: join existing transition candidates to trigger provenance.
5. **visible-object -> map-world coordinate conversion**: normalize actor/object coordinates into canonical map space.
6. **NPC/sprite/event/dialogue integrated object catalog**: merge currently separate semantic products.
7. **native `$0305` writer classification**: close remaining dynamic pack provenance.
8. **rebuild-spec integration**: externalize collision/trigger schema and unresolved gaps.

## Progress handling

No affected track percentage is increased this cycle because no new ROM-backed semantic closure occurred. The formal overall value remains whatever `progress/project_progress.json` currently exposes until that stale tracker is reconciled with the newer map/sprite/dialogue evidence. This cycle adds evidence and blocker state without treating a local planning milestone as whole-game completion.
