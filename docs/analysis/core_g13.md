# Core Goal13 model 260510Y

## Stable topology

```text
VM/config
→ bank87 slot loop
    → accumulation
    → compose flags
    → normalize flags
    → STA $0799
    → LDA $0799
    → AND #SKIP_MASK
    → BNE skip / append
→ append buffer
→ blob-runner traversal
→ OAM pre-registration
→ OAM emission
```

## Working visibility equation

```text
VISIBLE(slot[i]) =
  normalize(
    compose(
      macro[class],
      spatial,
      shared_state
    )
  ) & SKIP_MASK == 0
```

With:

```text
shared_state is monotonic within a frame
shared_state >= T forces SKIP for current and later slots
```

## Threshold model

```text
S(i) = Σ contribution[0..i]
K = first i where S(i) >= T
visible = [0 .. K-1]
skipped = [K .. N]
append_count = K
```

## $0799 role

`$0799` is treated as a canonical visibility staging bridge:

```text
finalized flags → $0799 → masked branch → append/skip
```

Current evidence supports:

- single canonical write
- single masked branch consumer
- no append-time recomputation
- no downstream normalization
- no late visibility restoration

## $0759 role

`$0759` is treated as append-gated execution dispatch:

```text
append traversal → JSR ($0759)
```

Thus invisible slots should never execute through `$0759` in the Goal13 path.

## 0x39850 macro rows

The scheduled analysis treats `0x39850` rows as accumulation-domain rows:

```text
macro row → contribution magnitude / threshold acceleration / class weighting
```

They are not currently treated as skip-encoding or canonical visibility rows.

## Primary target to extract

```asm
LDA $0799
AND #imm
BNE skip
```

Extracting `#imm` should resolve `SKIP_MASK`.

## Search signatures

### append_count RAM

```text
increment-on-append
stable after slot loop
consumed by blob runners
not used by VM scheduler
```

### shared_state RAM

```text
frame reset
monotonic increment
threshold-correlated plateau
no rollback/no decrement
```

### normalization block

```text
immediately before STA $0799
likely AND/ORA style flag shaping
```

