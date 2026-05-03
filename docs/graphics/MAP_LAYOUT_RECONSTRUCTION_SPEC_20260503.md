# Map layout reconstruction spec（2026-05-03）

## Input

```text
metatile_dictionary.csv
metatile_graph.csv
optional observed frame grid
```

## Deterministic algorithm

```text
seed: max-frequency metatile
expand order: right -> down -> left -> up
tie-break: edge frequency desc, metatile_id asc
constraint: no conflicting placement
```

## Output

```csv
scene,x,y,metatile_id,source,confidence
```

## Validation

- graph consistency
- tile continuity
- frame invariance
- DMA consistency
