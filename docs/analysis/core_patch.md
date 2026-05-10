# Goal13 patch-safety boundaries

## Absolute safe candidates

### Branch neutralization

```asm
BNE skip → NOP/NOP
```

Expected effect:

```text
all branch-skipped slots become append-eligible
```

Risk:

```text
OAM overflow or sprite corruption may appear downstream
```

### Pre-mask force visible

```asm
LDA #$00
```

immediately before:

```asm
AND #SKIP_MASK
```

Expected effect:

```text
masked result does not trigger skip
```

## Optimal safe candidate

### Pre-STA canonical override

Modify `flags_final` immediately before:

```asm
STA $0799
```

Advantages:

```text
preserves append semantics
preserves downstream assumptions
preserves deterministic traversal
keeps blob runners cardinality-passive
```

## Conditional risk

```text
append-buffer surgery
append_count edits
post-STA mutation
```

Possible failure modes:

```text
blob-runner desync
undefined traversal
OAM corruption
slot/behavior mismatch
```

## Unsafe first targets

```text
shared_state edits
normalization edits without mask knowledge
macro-row edits
VM/script edits
blob-runner edits
STA relocation
```

Reason:

```text
These risk breaking the architecture rather than only disabling the culling branch.
```

## Recommended next patch experiment

1. Locate `LDA $0799 / AND #imm / BNE skip`.
2. Confirm `#imm` by branch outcome traces.
3. Try branch neutralization in an emulator-only test.
4. Log append_count proxy and OAM overflow behavior.
5. If stable, move patch point earlier to pre-STA canonical override.

