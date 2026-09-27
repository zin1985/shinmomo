# Map pack-context reachability — 2026-09-28

Canonical ROM: 2,097,152 bytes, SHA-256
F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98.

This note connects the already-proven mode-state graph and CA:C000 inverse
resolver to the C4 VM's per-slot pack context.

## 1. Correction: master-pack loader entry is 84:8508

Older April notes described the CA:C000 master-pack loader as 84:8509.
Instruction alignment shows the actual entry is:

```
84:8508  STA $126A
84:850B  PHY
84:850C  STA $126E
...
```

84:84F5..8507 is a separate helper that returns before 8508.

Therefore the canonical loader entry is **84:8508**.

The full ROM contains exactly five direct JSL callers:

| runtime CPU | source supplied to 84:8508 |
|---|---|
| 81:96D1 | $0305 |
| 81:98DF | $0305 |
| 82:912B | immediate 0x19 |
| 84:871E | $126A |
| 85:CAC5 | immediate 0x14 |

The reproducible scan is in
`tools/python/catalog_map_pack_context.py`.

## 2. Mode entries now connect to pack normalization

The documented C0:CA69 state table gives states 0,1,2,3,5,6.

New pack-context links:

- state 0 / 81:964E reaches 81:96D1:
  `LDA $0305 ; JSL $84:8508`
  - pack source is dynamic $0305.
- state 1 / 82:8F1B unconditionally calls 82:90ED near entry.
  That routine reaches:
  `LDA #$19 ; JSL $84:8508`
  - pack source is fixed 0x19.
- state 5 / 85:CAA3 reaches:
  `LDA #$14 ; JSL $84:8508`
  - pack source is fixed 0x14.
- state 2 / 83:B7CD writes $1399=5.
- state 3 / 86:82E2 clears $1399 and jumps to the common transition path,
  therefore transitions to state 0.
- state 6 / 81:E331 writes $1399=5 and jumps to the common transition path.

This makes the coarse normalization graph:

```
state 0 -> dynamic pack $0305
state 1 -> fixed pack 0x19
state 2 -> state 5
state 3 -> state 0
state 5 -> fixed pack 0x14
state 6 -> state 5
```

This is a normalization/initialization relation, not yet a proof that every VM
slot executing under one state uses only that pack.

## 3. $126E is preserved per C4 VM slot

The decisive bridge is in the C4 VM scheduler.

### Save

At 84:8016:

```
PHX
LDX $9B
LDA $126E
STA $0759,X
PLX
RTS
```

So, in this specific C4 VM routine, **$0759,X stores the current pack id
$126E**.

### Restore

At 84:8070:

```
LDA $0759,X
STA $126E
STX $9B
...
```

The scheduler therefore restores each VM slot's pack context before executing
that slot.

This is intentionally handler-qualified. Existing WRAM work already proved
that $0759/$0799 are overlay columns with different meanings in other object
families. This result does not restore the old incorrect universal-pointer
interpretation.

## 4. Nested VM execution inherits pack context

The VM creation/entry path 84:8021..806F preserves the current $126E while
building a new execution slot, then calls 84:8076.

At 84:8086, after the slot index has been installed:

```
LDA $126E
STA $0759,X
```

Therefore nested/new C4 VM execution **inherits the current pack context** and
persists it in the new/current slot.

This explains why a later global mode transition does not imply that all live
VM slots immediately switch to a single pack.

## 5. Normal VM opcode 0x04 explicitly switches pack context

The normal C4 dispatch table maps opcode 0x04 to 84:89D6.

Handler:

```
84:89D6  LDA [$98],Y
84:89D8  STA $126E
84:89DB  JSR $8016
84:89DE  JMP $895E
```

84:895E advances by two bytes, so the instruction is:

```
04 <pack_id>
```

Effect:

```
operand -> $126E
        -> current slot $0759,X
```

Thus pack context can change inside an already-running VM stream independently
of the mode-entry normalization routine.

## 6. Consequence for the 137 unresolved primary selectors

The primary selector catalog starts at pack 0x28.

There are no primary selector candidates in:

- fixed state-5 pack 0x14;
- fixed state-1 pack 0x19.

That is useful context, but it is **not** enough to classify the 137 unresolved
rows as state 0.

Reason:

1. a VM slot preserves $126E across scheduler resumes;
2. nested VM execution inherits that pack id;
3. opcode 0x04 can explicitly change the slot's pack id;
4. $1398 is a global/current mode discriminator used by opcode >=0x50 dispatch.

So the correct reachability object is:

```
(mode state, VM slot, script pointer, pack id)
```

rather than:

```
pack id -> one fixed mode state
```

## 7. Relation to the inverse resolver

The parallel result in
`docs/analysis/map_pack_inverse_resolver_20260928.md` proves the other
direction:

```
current script pointer
-> CA:C000 master entry
-> pack id
-> $126E / $12B4
```

Combined with this pass:

```
script pointer <-> pack id
                 |
                 +-> $126E
                     |
                     +-> $0759,X per C4 VM slot
                     |
                     +-> inherited by nested VM execution
                     |
                     +-> changed by opcode 0x04
```

This closes the storage/inheritance side of pack reachability.

## 8. Next static target

The next highest-value proof is the **slot seed path**:

1. identify where a fresh slot's script pointer $98/$99/$9A is selected;
2. pair that pointer with the $1398 value at first dispatch;
3. emit reachable mode-state sets per pack/record/substream;
4. join those sets to the 118 unresolved record-0 selectors first;
5. retain multiple states wherever control flow permits more than one.

Until that join is complete, no bulk promotion of the remaining 137 primary
selectors is justified.

## Outputs

- `tools/python/catalog_map_pack_context.py`
- `data/maps/selectors/map_pack_context_summary.json`
- this document
