# DMA sequence synchronization spec（2026-05-03）

## sequence id rule

Increment `dma_sequence_id` when:

```text
DMA source address changed
DMA size changed
DMA target changed
frame gap > 1
manual scene transition marker exists
```

## join constraint

```text
VRAM + BG tilemap + CGRAM + OAM should share same dma_sequence_id
```

## Purpose

- VRAM/CHR/palette整合性保証
- frameズレによる誤色・誤tile結合の防止
- BG/OAM分離の安定化

## Output schema

```csv
frame,dma_sequence_id,channel,source_bank,source_addr,target,bbad,vram_word_addr,size_bytes,target_region,source_kind,notes
```
