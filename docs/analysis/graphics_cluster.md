# Sprite cluster, OAM attribution, and CHR atlas notes

## Cluster identity

`cluster_track_id` is the primary logical actor continuity key.

Stable during:

```text
OAM fragmentation
sprite clipping
priority contention
battle redistribution
CHR reassignment
overlay churn
repeated interruption chains
```

## Contribution estimates

`contribution_est` is treated as logical-entity bound rather than transient sprite-fragment bound.

Current hypothesis:

```text
large actor classes → larger contribution_est
small actor classes → lower contribution_est
```

This supports the `0x39850` contribution-weight hypothesis.

## OAM attribution

Stable mapping:

```text
cluster_track_id ↔ OAM ownership
```

OAM and CHR redistribution are downstream presentation layers. They do not appear to feed back into Goal13 branch logic.

## Battle CHR atlas

Battle CHR atlas grouping remains contribution-correlated and transition-stable. Exact CHR reuse saturation and palette overflow rules remain open.

