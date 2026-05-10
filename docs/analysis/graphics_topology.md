# Graphics topology and mapchip reconstruction

## Confirmed scheduled-analysis model

BG tilemap streaming is incremental and world-coordinate preserving.

Observed properties:

```text
localized horizontal/vertical update bands
spatially bounded invalidation
stable absolute tilemap_world coordinates
deterministic metatile convergence after interruption
field/town/indoor continuity
```

## Metatile pipeline

```text
VRAM/BG tilemap log
→ tilemap_world coordinate stitching
→ 2x2 metatile candidates
→ canonical metatile IDs
→ topology graph
→ scene/map reconstruction
```

## Transition behavior

Temporary uncertainty can occur during:

```text
overlay insertion
rapid directional reversal
partial BG stream interruption
battle transition overlays
compound BG/OAM churn
```

But scheduled outputs consistently treat this uncertainty as:

```text
transition-local
spatially bounded
resolved after stabilization interval
```

## Goal13 independence

Metatile convergence timing appears independent from append-boundary timing. This matters because topology latency should not be mistaken for Goal13 culling behavior.

