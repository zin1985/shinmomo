# Sprite clustering and CHR reconstruction plan（2026-05-03）

## 1. 目的

battle CHR atlas から、OAMを使ってキャラ・敵・UI数字・エフェクト単位のPNGを復元する。

## 2. 入力

```text
OAM snapshot CSV
OAM high table
OBSEL register ($2101)
VRAM dump
CGRAM dump
visible_objects.csv
```

## 3. クラスタリング優先順位

1. visible_object_id が一致するOAM piece
2. 座標距離が近い piece（±24pxを初期値）
3. palette が一致する piece
4. tile index が連続または近傍の piece

## 4. 配置ルール

タイル番号順ではなく、OAMの `(x,y)` を正とする。

```text
cluster origin = min(x), min(y)
local_x = x - origin_x
local_y = y - origin_y
```

## 5. 出力

```text
graphics/battle/reconstructed_sprites/*.png
data/csv/battle_sprite_clusters_20260503.csv
data/csv/oam_chr_mapping_20260503.csv
```
