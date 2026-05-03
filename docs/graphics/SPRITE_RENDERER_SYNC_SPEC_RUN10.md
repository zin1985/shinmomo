# Sprite renderer sync spec run10

## 目的

OAM由来のspriteを、実機に近い順序・座標で再構成する。

## Sort key

```text
1. priority
2. OAM index
```

## X座標9bit補正

```python
x = value & 0x1FF
if x >= 256:
    x -= 512
```

## CHR address式（暫定）

```text
chr_addr = (obj_base << 14) + (name_select << 13) + (tile_index << 5)
```

注意: `obj_base` と `name_select` は `$2101 OBSEL` とOAM high tableから確定する。

## 出力

```text
tools/python/sprite_renderer_sync_v1.py
data/csv/frame_comparison_run10.csv
graphics/battle/reconstructed_sprites/
```
