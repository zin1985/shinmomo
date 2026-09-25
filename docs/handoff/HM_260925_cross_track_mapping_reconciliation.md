# Cross-track historical mapping reconciliation handoff — 2026-09-25

## Purpose

This cycle re-integrated historical reverse-engineering results into the current rolling tracker before choosing new analysis targets.

The key lesson is that several current percentages and blockers had drifted behind work already completed in April/May. Historical results are now routed through one current architecture map:

`docs/analysis/cross_track_architecture_map.md`

## Canonical ROM

Canonical Drive folder is recorded in `progress/project_progress.json`.

This cycle confirmed:

- file: `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- Windows analysis copy SHA-256:
  `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM or raw copyrighted dump is committed.

## Major reconciliations

### Addressing

Use LoROM-corrected labels.

Examples:

- file `0x39850` = `87:9850`
- file `0x3F09A` = `87:F09A`
- file `0x41A10` = `88:9A10`
- file `0x487A2` = `89:87A2`

Do not copy old flat-bank labels without normalization.

### 41A10 versus VM reader

These are separate layers.

Unresolved:
- routine that scans/matches `88:9A10` 8-byte selector records.

Already known:
- target script VM reader:
  `89:87A2 -> 87BD -> 87CF -> 87D4`

The 398xx 9-byte-looking rows are normal VM macro rows rather than proof of a dedicated row reader.

### 0x300D3 pointer-like lead

Canonical-ROM revalidation confirms that record 17 of the `0x30048` 8-byte descriptor bundle contains `05 9A 88` at `0x300D3`, i.e. pointer-like `88:9A05`.

However, scanning all 35 records shows +3..+5 is not a universal valid LoROM pointer field. Treat this as a weak resource clue, not a confirmed 41A10 matcher bridge.

### 81:8D87

Historical analysis already characterized all four outputs:

- `$09`: available normal actor count
- `$0A`: normal actor count
- `$0C`: total logical object count
- `$0D`: special object count

This justifies restoring the current track from 30% to 85%.

### Condition dispatch

`85:86AC` is a generic condition evaluator.

For the entity field associated with `$180A[entity-1]`:

- 0x38: set selected bits
- 0x39: clear selected bits
- 0x3A: test selected bits clear

The common bit7 meaning is conservatively hidden/suppressed/unavailable-like.

This justifies restoring Condition Dispatch from 62% to 81%.

### Dialogue

Dialogue source reading is independent of the 41A10 selector matcher.

Known source reader core:

- `C9:9E10`: main source/control reader
- `C9:9E57`: raw source byte read
- `$B1/$B2/$B3`: 24-bit source pointer
- `C9:9F34`: dictionary token handling
- nested source-context stack around `$1274..`

The old progress note that treated 41A10 as the major dialogue blocker was removed.

### Object architecture

Keep two layers separate:

1. `$0619..$0A18`: 64-slot controller/object work SoA with handler-dependent overlays.
2. AF33 visible-object pool: up to 64 real objects plus physical sentinels 0/1.

Visible-object mapping:

`physical_node = external_handle + 2`

The active render path remains:

`$0A61 chain -> C0:B03D -> C0:B100 -> $0EE9 OAM mirror -> DMA`

Historical AF33 callers show that some controller slots store a visible-object external handle, giving an explicit bridge between these layers without making the pools identical.

## Progress reconciliation

This cycle primarily restores previously completed evidence into the current tracker.

- overall weighted progress: about 70.0% -> 74.6%
- ROM map: 72 -> 74
- Script VM/Event: 66 -> 67
- 81:8D87: 30 -> 85
- Condition Dispatch: 62 -> 81
- Dialogue: 58 -> 64
- Externalization: 66 -> 68
- Whole-game reconstruction: 76 -> 77
- Goal13 NPC/OAM remains 96

## Next priorities

1. Find the 41A10 selector matcher through indirect/generic resource traversal, or capture the reader PC with a runtime read breakpoint on `88:9A10` when a facility state is available.
2. Decode the 398xx high-op VM family using the already-known normal VM core.
3. Prove one controller/work slot -> AF33 external handle -> physical handle+2 -> OAM chain end-to-end.
4. Integrate the known C9 dialogue source reader into bulk extraction.
5. Continue weapon-special selector/commit semantics.
6. Continue universal-versus-overlay classification for the shared controller SoA.

## Do not regress

- Do not restart a generic 398xx 9-byte reader hunt.
- Do not treat `$0799` as a globally fixed visibility field.
- Do not identify the controller SoA with the visible-object active-list pool solely because both have capacity near 64.
- Do not block dialogue extraction on 41A10.
- Do not treat `0x300D3 -> 88:9A05` as a confirmed matcher connection without a consumer.
