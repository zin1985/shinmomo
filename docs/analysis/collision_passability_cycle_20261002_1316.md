# Collision / passability rolling cycle (2026-10-02 13:16 JST)

## Baseline refresh

Current main at cycle start is `93c5e43745fb2d3b2b2fae6d36658c464ee7f69f`. Recent parallel work already includes phase-aware Tabidachi dialogue, verified analysis-savestate WRAM patching, opcode59 bit7 palette-selector closure, controller-trailer dispatch classification, and the existing map/transition reconstruction. None of those completed layers are reimplemented here.

`progress/project_progress.json` remains dated 2026-09-27 and is stale relative to current evidence.

## Canonical ROM availability

Required ROM is `Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

Mole Remote v0.3.0 health succeeded. A filesystem probe of the currently visible `G:\`, `C:\Users\zin\Google Drive`, and `C:\Users\zin\My Drive` roots returned `ROM_NOT_FOUND`. Therefore this cycle did not use a ROM and did not substitute another ROM. No ROM-backed address/table semantic is promoted.

## Static narrowing while ROM is unavailable

A repository search still finds no promoted canonical collision/passability schema. However, the current machine-readable tracker already records a useful WRAM boundary: `$07D9/$0819` are movement-work columns in the 64-slot SoA object pool, while `$0919/$0959` are position-like columns. This is not proof that any of these fields is the collision discriminator, but it sharply reduces the first dynamic capture set once the canonical ROM becomes visible.

### Confirmed

- `$0619..$0A18` is tracked as a 64-slot x 16-column SoA object pool.
- `$07D9/$0819` have existing movement-work evidence.
- `$0919/$0959` have existing position-like evidence.
- No canonical collision/passability schema is currently promoted in main.
- The required Drive ROM was not accessible in this cycle; no substitute ROM was used.

### Strong hypothesis

For a same-savestate one-input control pair, the highest-information first watch set is the active object's `$07D9/$0819/$0919/$0959` tuple plus already-known map/config state. If blocked movement changes movement-work without committing the position-like pair, the accept/reject branch can be localized before expanding to wider WRAM. If neither pair distinguishes the cases, widen capture rather than assigning collision semantics prematurely.

### Unconfirmed

- which movement-work byte/bit, if any, carries accept/reject state;
- collision/passability reader address and record format;
- terrain/metatile attribute vs object occupancy vs event/transition gate composition;
- event-trigger-region record format;
- shared visible-object to map-world coordinate normalization.

## Next executable experiment

1. verify the canonical ROM size/hash;
2. load one deterministic field savestate;
3. identify the active object slot without assuming slot 0;
4. capture `$07D9/$0819/$0919/$0959` for that slot;
5. replay exactly one walkable direction and one blocked direction from the same state;
6. compare movement-work mutation against committed position mutation;
7. only after a reproducible discriminator appears, trace its writer/reader and join it to map/config data.

This experiment deliberately starts from already evidenced WRAM columns instead of a blind whole-WRAM diff, while retaining fail-closed semantics.

## Rolling priority

1. collision/passability movement accept/reject path using the focused WRAM watch set above;
2. map/config -> collision-data crosslink and metadata-only exporter;
3. event-trigger-region reader/record format;
4. transition -> event/trigger crosslink expansion;
5. visible-object coordinate -> map-world coordinate conversion;
6. NPC/sprite/event/dialogue integrated object catalog;
7. native `$0305` writer classification;
8. rebuild-spec integration.

## Progress policy

This cycle narrows the executable experiment but does not close a collision semantic layer. Formal percentages remain unchanged until ROM-backed evidence or tracker reconciliation justifies a change.