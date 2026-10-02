# Opcode 0x59 field06D9 direct direction reader (2026-10-02)

## Scope

This note closes the missing handler-local reader for the fourth operand of the normal six-byte opcode-0x59 actor command.

The conclusion is intentionally scoped to the opcode-0x59-created C1 actor/controller overlay. It does **not** assign a universal meaning to the shared WRAM column `$06D9,X`.

## Dispatch split

The VM has two different meanings for opcode `0x59`.

For the normal event VM path, when `$1398 == 0`, the normal dispatch table at `84:87D4` selects `84:8F93`. That routine reads five operand bytes into `$1856..$185A`, copies the current 24-bit pointer into `$185B..$185D`, advances the VM pointer by six bytes total, and calls `81:ADBD`.

The established `81:ADBD` allocation path stores the fourth opcode-0x59 operand from `$1859` into `$06D9,X`.

For the special path, when opcode >= `0x50` and `$1398 != 0`, the dispatcher routes through `82:8000`. Special opcode `0x59` selects `82:834A`, which calls `80:BBA4`, `84:9BCE`, and `84:9BC5`. That is a separate command meaning and must not be used to infer actor-field semantics.

## Direct C1 reader

The missing direct reader is present in the opcode-0x59 controller update family.

At `C1:B01A` the controller reads `$06D9,X`, doubles it, and uses it to index a two-component delta table:

```text
C1:B01A  LDA $06D9,X
C1:B01D  ASL A
C1:B01E  TAX
C1:B01F  LDY $6A
C1:B021  LDA $B038,X
           JSL $80:BBEC
C1:B028  LDA $B039,X
           JSL $80:BC21
```

For the only values seeded by the 817 static opcode-0x59 actors, the selected pairs are:

| field06D9 | first delta | second delta | cardinal interpretation |
| ---: | ---: | ---: | --- |
| 1 | +1 | 0 | right |
| 2 | 0 | +1 | down/front |
| 3 | -1 | 0 | left |
| 4 | 0 | -1 | up/back |

The table stores negative unit deltas as nibble `0x0F`. The `80:BBEC` and `80:BC21` helpers sign-extend the low nibble and add the components into coordinate accumulator families. This is direct movement/coordinate use, not only a visual sprite correlation.

## Independent forward-position projection

A second reader independently uses the same field as a cardinal projection selector.

At `C1:B25A` and `C1:B26C`, `$06D9,X` is doubled and used to add direction-dependent offsets to the actor coordinates derived from `$0699,X` and `$0659,X`. The projected values are written to the `$0314/$030D` and `$0313/$030B` coordinate pairs.

This independently confirms that the opcode-0x59 overlay treats the field as a cardinal direction value in controller logic.

## Evidence boundary

The opcode-0x59 field can now be promoted from a strong candidate to:

`confirmed_handler_local_direction_seed`

with the mapping:

- 1 = right
- 2 = down/front
- 3 = left
- 4 = up/back

The existing runtime evidence remains compatible: pack-0x50 actors with value 2 render confirmed front frames in three separate selector families.

Two restrictions remain important:

1. Do not rename the shared WRAM column globally. A separate C0 handler initializes `$06D9,X` to `0xFE` and uses it as a script/table cursor.
2. Do not narrow this to a sprite-facing-only field. The direct C1 readers prove movement and forward-coordinate projection use. It is safe to call it a handler-local direction seed/selector; a more exclusive game-facing label would overstate the evidence.

## field0719 relation

This finding does not change the conservative interpretation of the fifth operand. The opcode-0x59 path seeds `$0719,X`, and the confirmed C1 bridge copies its low two bits into mutable `$0759` controller low state. The game-facing meaning of those low-state alternatives remains unresolved.

## Provenance

Canonical ROM used for the direct byte-level verification:

- `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, raw emulator dump, or copyrighted raw payload is committed.
