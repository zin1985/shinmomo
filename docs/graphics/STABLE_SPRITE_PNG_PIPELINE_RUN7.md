# Stable sprite PNG pipeline run7

## 問題

OAM / VRAM / CGRAM がフレーム単位で揺れると、PNGが壊れる。

## 解決

`stable_frame_flag` を導入する。

```text
stable_frame_flag =
  bg_hash unchanged
  and oam_hash unchanged
  and cgram_hash unchanged
  and dma_count <= threshold
```

## 出力単位

```text
frame / object_id / cluster_id
```

## Crop

OAM座標の bounding box でcropする。空白を減らし、キャラ単位のPNGとして扱えるようにする。
