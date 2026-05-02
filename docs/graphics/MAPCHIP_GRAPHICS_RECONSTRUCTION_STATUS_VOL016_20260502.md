# Mapchip / graphics reconstruction status vol016（2026-05-02）

## 状態まとめ

vol016では、グラフィック復元の主戦場を **ROM静的推測** から **runtime snapshotベースの復元** へ寄せた。

現在の軸:

```text
Lua polling log
  -> VRAM/CGRAM/OAM/PPU/BG/DMA snapshot
  -> tilemap entry decode
  -> tile usage / metatile candidate
  -> BG layer / object layer separation
  -> color PNG reconstruction
```

## できたこと

- field VRAM tilemap decode CSV化
- field 2x2 metatile candidate可視化
- battle 4bpp linear sheet / backdrop / UI glyph候補可視化
- static ROM 2bpp/4bpp candidate contactsheet出力
- DA:3800 stream候補画像の整理
- current character pseudo-color candidate出力
- Lua unified polling loggerを追加
- tile adjacency -> tilemap inference stageを追加

## 未完

- town / indoor / field / battle の同一フォーマットsnapshot採取の横並び比較
- CGRAM palette適用
- BG layer別の完全分離
- ROM asset source -> DMA -> VRAM配置の完全接続
- NPC/OAM負荷軽減patchの安全化

## 次の判断基準

- BG hashが変化し、OAMが安定: mapchip/BG更新
- OAMが変化し、BG hashが安定: NPC/object更新
- DMA sourceが `7E:xxxx`: 展開済みWRAM staging。さらに上流追跡が必要
- DMA sourceが `C0-DF` / `80-9F`: ROM側asset source候補
