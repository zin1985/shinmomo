# Battle CHR / OAM attribution plan vol016（2026-05-03）

## 1. 背景

run2で解析した `vram.bin` は field mapchip型ではなく battle CHR型 snapshot とみなすのが自然だった。battle側では tilemap推定より先に、OAMとCHR atlasを対応づける。

## 2. 暫定VRAM region label

```text
0x0000..0x7FFF : battle_chr_0000_7fff          : backdrop / battle UI / glyph CHR候補
0x8000..0xAFFF : battle_ui_glyph_8000_afff     : UI/glyph/補助タイル候補
0xB000..0xBFFF : empty_b000_bfff               : ほぼ空き
0xC000..0xDFFF : battle_object_ui_c000_dfff    : character/object/number/status候補
0xE000..0xEFFF : empty_e000_efff               : ほぼ空き
0xF000..0xFFFF : special_f000_ffff             : stripe/fill/special pattern候補
```

## 3. OAM attribution CSV schema

```csv
frame,slot,x,y,tile,attr,palette,priority,hflip,vflip,size,chr_vram_word,chr_vram_byte,region_label,visible_object_id,visible_object_type,note
```

## 4. 判定ルール

```text
OAM変化あり・BG hash安定      -> object/NPC/actor candidate
BG hash変化あり・OAM安定      -> mapchip/BG/backdrop candidate
DMAあり・VRAM 0xC000..0xDFFF  -> battle object/UI CHR update candidate
DMAあり・VRAM 0x0000..0x7FFF  -> backdrop/glyph/base CHR update candidate
sourceが7E/7F                 -> WRAM staging 展開済み素材
sourceが80-9F/C0-DF           -> ROM direct asset candidate
```

## 5. 必須追加ログ

- `$2101` OBSEL
- OAM high table
- sprite size bit
- name select / OBJ base
- CGRAM full snapshot
- stable frame flag
