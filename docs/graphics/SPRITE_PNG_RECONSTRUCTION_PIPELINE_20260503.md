# Sprite PNG reconstruction pipeline（2026-05-03）

## Pipeline

```text
OAM tile/attr/x/y
-> OBSEL + OAM high table
-> CHR VRAM byte address
-> 4bpp decode
-> palette apply from CGRAM
-> OAM (x,y) compositing
-> crop bounding box
-> PNG
```

## Stable frame selection

PNG化には安定フレームを選ぶ。

```text
- DMA発生なし、または最小
- BG hash が前後で安定
- OAM hash が前後で安定
- CGRAM hash が前後で安定
```

## Palette

CGRAM未取得時は疑似パレットで出す。CGRAM取得後に同じcluster_idへ実色PNGを上書きせず、別ファイル名で保存する。

```text
cluster_0001_pseudo.png
cluster_0001_cgram.png
```
