# Collision/passability rolling cycle 2026-10-02 21:11 JST

## Selected theme
Separate the already-confirmed native map-boundary accept/reject path from the unresolved bank89 object-geometry candidate, then redirect the next static work to boundary -> event/trigger crosslinks.

## Confirmed facts

- `data/maps/transitions/pack2e_centerline_return_closure_20261002.json` proves a concrete native south-boundary path for pack `0x2E`: `C1:8943` copies current map X/Y to `$030B/$030D`; `81:81DD` compares against inclusive `$15CA..$15CD` bounds; `C1:8955` calls `81:895A` when outside; the request then reaches the saved-state restore path and restores the destination pack through `C1:8255`.
- The same witness fixes pack `0x2E` bounds at X `0..19`, Y `0..12`, with the center south step `(9,12)->(9,13)` outside Y bounds.
- `docs/analysis/wram_object_pool.md` separately records bank89 `$0919/$0959` position-like work and a later `$0959` / `$0959+$09D9+1` edge/extent probe.
- The repository does not preserve concrete bank89 routine/caller provenance for that sentence, and the committed 80-bank disassembly is insufficient to reconstruct it.
- Google Drive search and local synced-drive probes did not expose `Shin Momotarou Densetsu (J)_original.smc`; no substitute ROM was used.

## Interpretation

**Strong conclusion:** the confirmed native *map boundary* discriminator is already known and uses `$030B/$030D` plus `$15CA..$15CD`. It should not be rediscovered through the bank89 `$0959/$09D9` lead.

**Strong hypothesis:** the bank89 lead is more likely an object/geometry overlay or another spatial consumer than the canonical map-bounds test. This is not enough to label it object collision.

**Unconfirmed:** terrain/metatile passability, object occupancy collision, and event-trigger region semantics remain separate unresolved layers.

## Consequence for schedule

The highest-information static task while the canonical ROM is unavailable is now `native map-boundary -> event/trigger crosslink`, using the already-confirmed C1/81 chain and transition witnesses. The bank89 provenance task remains queued but is explicitly blocked on missing committed provenance or canonical-ROM runtime evidence.

## ROM status

Drive??ROM????????????Expected size: `2,097,152` bytes. Expected SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`. Hash verification was not possible and no alternate ROM was used.
