# Opcode 0x59 controller trailer key semantics (2026-10-02)

## Scope

This note closes the caller-side structural meaning of the recurring event-record trailer:

```text
7A <body16>
7C <next_record_plus_1_16>
00
```

The target geometry was already proven by `catalog_event_record_frames.py`:

- `0x7A` target = the current record body immediately after the seven-byte trailer;
- `0x7C` target = one byte after the next record's `0xB0` start marker;
- `0x00` = keyed-table terminator.

The findings below classify the proven callers without assigning broader story semantics.

## 0x7A: map-entry record-body dispatch

The fixed caller is:

```text
C1:AEDC  LDA #$7A
         JSL $84:858D
         RTL
```

`84:858D` is the bank-safe wrapper around `84:859A`, the already-proven current-pack entry scanner. `84:859A` stores the requested entry id in `$126B`, starts from record index zero, walks the current pack's record-pointer structure, and uses the same `[entry_id][target16]...00` grammar whose reader is closed at `84:8699`.

The only direct JSL caller found for `81:AEDC` is at `C1:970F`, inside the high-level C1:96xx map-entry/native initialization chain. The same surrounding chain performs current-map/pack setup and separately requests other initialization entries such as `0x88`.

Because the trailer's `0x7A` target is exactly the current record body, the safe structural label is:

`map_entry_record_body_dispatch`

This says what is proven: during the map-entry initialization chain, the engine requests entry id `0x7A` through the pack-level scanner, and a matching record dispatch begins at that record's own body.

Do **not** rename this to "spawn" or "NPC init" globally. Record bodies can contain conditions, actor creation, event setup, and other VM work.

## 0x7C: front-interaction dispatch

The fixed actor/controller caller is reached through `C1:A1ED`.

The probe routine beginning at `C1:A204`:

1. reads the player direction from `$15C7`;
2. converts it through the cardinal delta table;
3. adds the delta to `$0313/$0314`, producing the tile immediately in front of the player;
4. calls the target/event lookup path around `81:B14F`;
5. when an opcode-0x59 actor/controller is selected, reloads its inherited event pointer:
   - `$0799,X -> $A4`
   - `$07D9,X -> $A5`
   - `$0819,X -> $A6`
6. marks controller state bit `$0759,X |= 0x20`;
7. returns success.

Only on that successful front-target path does the caller request key `0x7C`:

```text
C1:A1ED  JSR $A204
         BCC no_target
C1:A1F2  LDA #$7C
         JSL $84:867D
```

`84:867D/8699` then resolves `0x7C` inside the selected event/controller's keyed table.

The safe structural label is:

`front_interaction_dispatch`

This is stronger than the previous family-specific dialogue observation. It explains why `0x7C` can lead to NPC dialogue: the caller is the front-facing interaction probe. It must still not be renamed globally to "talk", because the target script may implement dialogue, service behavior, a reaction, or another interaction.

## Family 0x4E concrete witness

The previously closed family-0x4E table provides a concrete end-to-end witness:

```text
controller pointer CC:1B24
  -> key 0x7C
  -> target CC:1B42
  -> A4 17
  -> recovered dialogue source 0x4E:17
```

This is now understood as one instance of the general front-interaction path rather than an isolated dialogue coincidence.

## 0x00: terminator

The generic matcher at `84:8699` reads keyed entries with a three-byte stride:

```text
[key:1][target16:2]
```

A key byte of `0x00` terminates the table and reports no further match.

The safe label remains:

`keyed_dispatch_terminator`

## Result

For the opcode-0x59 event/controller ancestry, the recurring trailer now has caller-backed structural semantics:

| key | target geometry | proven caller-side role |
| --- | --- | --- |
| `0x7A` | current record body | `map_entry_record_body_dispatch` |
| `0x7C` | next record + 1 | `front_interaction_dispatch` |
| `0x00` | none | `keyed_dispatch_terminator` |

These labels are intentionally structural. They do not imply that every `0x7A` body creates an actor or that every `0x7C` target is dialogue.

## Provenance

Canonical ROM used for direct byte-level verification:

- `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

Existing repository evidence used:

- `docs/analysis/event_controller_pointer_bridge.md`
- `docs/analysis/map_pack_entry_paths_20260928.md`
- `tools/python/catalog_event_record_frames.py`

No ROM, savestate, raw emulator dump, or copyrighted raw payload is committed.
