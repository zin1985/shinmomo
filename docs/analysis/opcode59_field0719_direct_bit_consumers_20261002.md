# Opcode 0x59 field0719 direct bit consumers (2026-10-02)

## Scope

This note classifies the directly visible consumers of the fifth operand of the normal six-byte opcode-0x59 actor command.

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

The random candidate is reduced to values 1..4, which are independently confirmed as the opcode-0x59 controller's cardinal direction values.

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

`80:AF0C` is the established animation-script update routine. It operates on the current animation-script cursor/duration fields, advances the cursor by a two-byte frame/duration pair when the duration expires, reloads the next pair, loops at a zero terminator, or decrements the active duration counter.

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

## bit7: OBJ palette-cache half selector

The previous direct-reader-only scan missed an earlier use in the opcode-0x59 allocation path itself.

Before `$185A` is stored into `$0719,X`, `81:ADBD` derives an eight-slot resource-selection mask from the sign bit of the fifth operand:

```text
81:AE30  LDA #$0F
         STA $1111
         LDA $185A
         BPL bit7_clear
         LDA #$F0
         STA $1111
bit7_clear:
         LDA $185A
         STA $0719,X
```

Therefore:

- bit7 clear -> `$1111 = 0x0F` -> resource slots 0..3 eligible
- bit7 set   -> `$1111 = 0xF0` -> resource slots 4..7 eligible

The allocation helper `80:B42D` treats `$1111` as a bitmask while scanning eight cache entries. The slot metadata live in the `$7E:23C2/$7E:23CA/$7E:23D2` families. On a new allocation, the selected slot index is converted to a color destination:

```text
TXA
ASL
ASL
ASL
ASL
ADC #$80
STA $0F
JSL $80:B35C
```

So the destination is:

`0x80 + slot * 16`

`80:B35C -> 80:B3A6` copies the resource data into the palette shadow at `$7E:21C2`; the downstream DMA path writes that shadow to SNES CGRAM via `$2122`. The `0x80..0xFF` color-index range is the OBJ half of CGRAM, split naturally into eight 16-color OBJ palettes.

The returned cache slot is also stored into the display object's `$0D27,Y` resource/asset-handle field by the `80:BCA3` path.

This closes the safe handler-local structural meaning of field0719 bit7 as:

`obj_palette_cache_half_selector`

More specifically, it constrains palette allocation/search to OBJ palette slots 0..3 or 4..7. This is not a movement, dialogue, spawn-condition, or actor-identity bit.

Do not overstate this as a specific visible recoloring rule: actors may reference identical palette resources in either half, and the reason for keeping the two cache halves separate is not yet proven.

## Evidence boundary

Confirmed handler-local structural labels for opcode-0x59 field0719 are now:

- bit7: `obj_palette_cache_half_selector`
- bit6: `double_animation_script_update_branch`
- bit4: `suppress_autonomous_random_direction_selection`
- bit0 / low2: `controller_low_state_seed`

Still unresolved:

- the higher-level gameplay reason for selecting lower vs upper OBJ palette-cache half
- a user-facing semantic name for the mutable low-state alternatives
- whether the bit6 branch yields an exact visible 2x animation rate

Do not generalize these bit meanings to every use of the shared WRAM column outside the proven opcode-0x59 actor/controller ancestry.

## Provenance

Canonical ROM used for direct verification:

- `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

Existing repository evidence used to classify `80:AF0C` includes the committed animation-script analysis that identifies the frame/duration pair format, cursor, current-frame field, and duration counter.

No ROM, savestate, raw emulator dump, or copyrighted raw payload is committed.
