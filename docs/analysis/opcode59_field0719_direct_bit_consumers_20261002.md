# Opcode 0x59 field0719 direct bit consumers (2026-10-02)

## Scope

This note classifies the directly visible C1 consumers of the fifth operand of the normal six-byte opcode-0x59 actor command.

The field is stored by the established normal opcode-0x59 path as:

`$185A -> $0719,X`

The static 817-actor corpus seeds only bits 7, 6, 4, and 0:

| seed bit | actor rows | source values |
| ---: | ---: | --- |
| bit7 | 43 | 0x80, 0x90 |
| bit6 | 18 | 0x41, 0x50 |
| bit4 | 589 | 0x10, 0x50, 0x90 |
| bit0 | 5 | 0x41 |

Bits 5, 3, 2, and 1 are not seeded by the current opcode-0x59 static actor corpus.

## bit4: autonomous random-direction selection gate

The regular C1 actor/controller update path calls the routine containing `C1:AF64`.

Relevant flow:

```text
C1:AF5E  LDA $0759,X
         BIT #$E0
         BNE return
C1:AF64  LDA $0719,X
         AND #$10
         ORA ...global/controller gates...
         BNE return
         ...
         JSL $80:BB68
         AND #$03
         ...
         JSL $80:BB68
         ...
         JSL $80:BB68
         ...
         JSL $80:BB68
         AND #$03
         INC A
         ...
         JSL $81:AFE6
```

The called helper at `C1:AFE6` stores its A input into `$06D9,X` and sets bit4 of `$0759,X`:

```text
C1:AFE6  STA $06D9,X
         LDA $0759,X
         ORA #$10
         STA $0759,X
         RTL
```

The random candidate is reduced to values 1..4, which are now independently confirmed as the opcode-0x59 controller's cardinal direction values.

Therefore field0719 bit4 has a direct structural meaning:

`suppress_autonomous_random_direction_selection`

When the seed bit is set, this particular autonomous/random direction-start path exits before choosing a fresh 1..4 direction. This does **not** mean the actor is globally stationary: scripted/controller-driven movement may still exist through other paths.

## bit6: double animation-script update branch

At `C1:B0EC`, the controller directly tests bit6:

```text
C1:B0EC  LDA $0719,X
         BIT #$40
         BEQ normal_branch
         JSL $80:AF0C
         JSL $80:AF0C
         BRA done
normal_branch:
         JSR $B101
```

`80:AF0C` is the existing animation-script update routine. It operates on the current animation-script cursor/duration fields, advances the cursor by a two-byte frame/duration pair when the duration expires, reloads the next pair, loops at a zero terminator, or decrements the active duration counter.

The safe structural classification for field0719 bit6 is therefore:

`double_animation_script_update_branch`

The code directly proves two successive animation-script update calls are selected in this branch. A user-facing label such as "double animation speed" is still stronger than the current evidence because the total call cadence and all surrounding update paths have not been normalized.

## low bits: controller low-state seed

The already committed ROM closure remains valid.

At `C1:B309`:

```text
LDA $0719,X
AND #$03
ORA $0759,X
STA $0759,X
```

Thus the low two bits feed mutable `$0759` controller low state after selected destination bits are cleared. In the current static actor corpus only bit0 is seeded; bit1 is not.

Use the existing conservative label:

`controller_low_state_seed`

A later path can overwrite these low bits, so this is an initial controller-state contribution, not a permanent mode identity.

## bit7: direct consumer still unresolved

The C1 scan of direct `LDA $0719,X` readers finds tests of bit4, bit6, bit5, bit3, and the low two bits. Bits5 and3 are runtime-state consumers but are not seeded by the current opcode-0x59 actor corpus.

No direct C1 `$0719,X & #$80` / `BIT #$80` consumer was found in this pass.

This does not prove bit7 is unused. It may be copied into another work byte, consumed through a different addressing form, or used by another controller stage. Keep bit7 unresolved rather than assigning a behavioral label.

## Evidence boundary

Confirmed handler-local structural labels for opcode-0x59 field0719 are now:

- bit4: `suppress_autonomous_random_direction_selection`
- bit6: `double_animation_script_update_branch`
- bit0 / low2: `controller_low_state_seed`

Still unresolved:

- bit7 game-facing/controller meaning
- a user-facing semantic name for the mutable low-state alternatives
- whether the bit6 branch yields an exact visible 2x animation rate

Do not generalize these bit meanings to every use of the shared WRAM column outside the proven opcode-0x59 C1 controller ancestry.

## Provenance

Canonical ROM used for direct verification:

- `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

Existing repository evidence used to classify `80:AF0C` includes the committed animation-script analysis that identifies the frame/duration pair format, cursor, current-frame field, and duration counter.

No ROM, savestate, raw emulator dump, or copyrighted raw payload is committed.
