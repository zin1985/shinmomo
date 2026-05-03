# Sprite atlas pipeline run8

## 目的

単発PNGを再利用可能な asset にする。

## 出力

```text
graphics/battle/atlas/enemy_atlas_00.png
graphics/battle/atlas/ally_atlas_00.png
graphics/battle/atlas/ui_atlas_00.png
data/csv/battle_sprite_atlas_metadata_run8.csv
```

## metadata schema

```csv
atlas_id,cluster_id,x,y,w,h,palette,object_type,source_frame,source_slots,confidence
```

## object_type

```text
enemy
ally
ui_number
ui_icon
effect
unknown
```
