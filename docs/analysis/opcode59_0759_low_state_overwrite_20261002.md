# Opcode 0x59 `$0759` low-state overwrite audit (2026-10-02)

## Provenance

Canonical ROM used directly this cycle:

- file: `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, or raw emulator dump is committed.

## Confirmed

The prior closure remains valid: C1:B301 clears selected bits of `$0759,X`, and C1:B309 copies `$0719,X & #$03` into the low two bits of `$0759,X`.

A fresh canonical-ROM window at file offset `0x01B360` clarifies the later C1:B36B/B376 path:

```text
C1:B36B  LDA [$0F],Y
         STA $00
         LDX $187E
C1:B376  LDA $0759,X
         AND #$FC
         ORA $00
         STA $0759,X
         JSR $B3C5
         RTS
```

This path is not a semantic consumer of the low bits seeded at C1:B309. It clears `$0759` bits 0-1 and replaces them from another local value loaded through `[$0F],Y` before entering the B3C5 path. Therefore C1:B376 must not be cited as evidence that the original opcode-0x59 bit0 seed selects the B3C5 behavior.

The B3C5 helper itself maps A={1,2,4} into a small local delta and updates the `$0919/$0959` pair; this is downstream of the replacement value, not proof of the earlier seed's game-facing meaning.

## Strong hypothesis

`$0759` low bits are a mutable controller substate field. Opcode 0x59 supplies its initial low state from `$0719`, while at least one later controller path can replace that state from script/controller-local data.

## Not yet confirmed

- The first read that semantically distinguishes the original C1:B309-seeded low state before any overwrite.
- A game-facing label for `$0759` bits 0-1.
- Whether the initial bit0 seed survives long enough in every opcode-0x59 controller path to affect visible behavior.

## Evidence boundary

Use the conservative label `controller_low_state_seed` for opcode-0x59 `$0719` bit0. Keep the C1:B309 transfer as confirmed, but do not infer movement/animation/execution semantics from C1:B376.

## Next frontier

The opcode-0x59 field audit has diminishing information gain. Unless a direct pre-overwrite low-bit reader is found quickly, retain bit0 as `controller_low_state_seed` and move the primary frontier to collision/passability and event-trigger-region reconstruction, joining it to canonical map configurations and transition/event crosslinks.
