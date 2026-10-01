# Opcode 0x59 `$0719` bit0 ROM closure (2026-10-02)

## Provenance

Canonical ROM used for this cycle:

- file: `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, VRAM/OAM/CGRAM dump, or copyrighted raw payload is committed here.

## Confirmed

The previously unresolved bridge at C1:B309 is present in the canonical ROM. File offset `0x01B301` decodes as the following relevant sequence:

```text
C1:B301  LDA $0759,X
         AND #$BC
         STA $0759,X
C1:B309  LDA $0719,X
         AND #$03
         ORA $0759,X
         STA $0759,X
         RTS
```

Therefore the low two bits of `$0719,X` are copied into the low two bits of `$0759,X`, after the destination low bits have been cleared. In the opcode-0x59 seed population previously catalogued, bit0 is present while bit1 is not observed as a seed bit. For that population, bit0 is therefore a confirmed contributor to `$0759` low state.

The same local controller area also contains direct `$0759,X` consumers. Examples include C1:B2A9, which tests bit6 and then masks/combines the value before timer/state work, and C1:B376, which replaces the low two bits from another local value before calling the B3C5 path. This confirms that `$0759` is an active controller-state byte in this handler family rather than a dead copy target.

## Strong hypothesis

For opcode-0x59 actors, `$0719` bit0 selects one of the low controller-state alternatives carried in `$0759`. This is stronger than the previous evidence boundary because the transfer itself is now ROM-confirmed. A game-facing label such as movement mode, execution mode, or animation mode is still premature until the downstream low-bit consumers are classified by behavior.

## Not yet confirmed

- The semantic name of `$0759` low bits.
- Whether the low-bit value directly selects a dispatch target or only modifies a subordinate controller mode.
- Runtime examples tying bit0=0/1 to a visible NPC behavior.

## Evidence boundary correction

This supersedes the uncertainty recorded in `opcode59_0719_bit0_evidence_audit_20261002.md`: the C1:B309 bridge is now directly reproduced from the canonical ROM. The earlier caution about not conflating unrelated `$0759` uses remains valid; only the C1 controller-local ancestry is claimed here.

## Next

1. Trace the first C1-local consumers that distinguish `$0759 & #$03` and classify the resulting branches.
2. If no clean game-facing label emerges quickly, mark bit0 as `controller_low_state_seed` and close the opcode-0x59 field audit conservatively.
3. Move the primary analysis frontier to collision/passability and event-trigger regions, joining those results to canonical map configurations and transition/event crosslinks.
