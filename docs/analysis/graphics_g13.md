# Graphics-side Goal13 support 260510Y

## Purpose

Graphics/mapchip analysis provides runtime bridge material for narrowing the core bank87 Goal13 branch without needing high-density raw dumps.

## Stable narrowing pair

```text
execution_frame + cutoff_index
```

Observed to survive:

```text
overlay churn
warp chaining
partial BG invalidation
battle redistribution
rapid directional reversal
compound BG/OAM redistribution
synchronized rendering interruption
synchronized overlap redistribution
repeated interruption churn
overlay interruption chains
```

## Minimal bridge fields

```text
execution_frame
cutoff_index
rank
termination_flag
contribution_est
S(i)
```

These fields preserve:

```text
append boundary
threshold plateau
branch narrowing windows
cluster continuity
```

## Core target supported

```asm
STA $0799
LDA $0799
AND #SKIP_MASK
BNE skip
```

The graphics bridge should be used to locate frames where cutoff occurs, then inspect the bank87 branch window.

## Append reconstruction

Visible-object summaries provide:

```text
append_count proxy ≈ first skipped rank
```

Stable fields:

```text
rank
cluster_track_id
termination_flag
```

## Non-causal graphics layers

The scheduled analysis treats these as downstream/presentation-only for Goal13:

```text
DMA
VRAM uploads
CGRAM updates
CHR atlas redistribution
OAM emission
```

They help observe consequences, not branch decisions.

