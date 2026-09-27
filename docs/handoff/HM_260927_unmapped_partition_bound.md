# Unmapped callsite partition bound — 2026-09-27

## Confirmed

- Current event crosslink leaves 1,078 source-reader-validated A4 callsites outside the B0/trailer frame grammar.
- Keyed-dispatch catalog exposes 34 direct A4 target pairs.
- Even if all 34 belong to the 1,078-callsite complement, direct keyed A4 targets explain at most 34/1,078 = 3.15%.
- Therefore at least 1,044 callsites require explanation beyond direct keyed A4 targets. This is a lower bound because any overlap with already mapped B0/trailer callsites increases the residual.

## Strong evidence

The next high-information operation is exact intersection/subtraction followed by residual clustering by local opcode sequence, family, boundary/transition shape and terminator pattern. Keyed dispatch should remain provenance evidence, but not the primary grammar hypothesis for the whole complement.

## Unresolved

- exact keyed-target intersection with the 1,078 complement;
- number and semantics of complementary grammars in the residual;
- runtime reachability and player-visible classification.

No ROM bytes, decoded dialogue bodies, savestates, SRAM, VRAM, OAM or CGRAM dumps are stored here.
