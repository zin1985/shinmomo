# Map validation spec（2026-05-03）

## Checks

1. adjacency一致
2. tile連続性
3. frame不変性
4. DMA整合性
5. CGRAM palette consistency
6. BG/OAM separation consistency

## Output schema

```csv
scene,frame_range,passed,issues_count,adjacency_score,tile_continuity_score,dma_consistency_score,palette_consistency_score,notes
```

## Pass policy

- `passed=true` は all checks が thresholdを超えた場合のみ。
- mismatch がある場合は `issues_count` と notes に残す。
- Goal12を完全完了扱いにする場合は、field/town/indoor/battle の代表sceneで pass すること。
