# 新桃太郎伝説 vol016 graphics担当スレッド 継続引継ぎ run2 (2026-05-02)

## 方針

別スレッドとの合意に従い、このスレッドは「画面にどう出るか」を担当する。
今回の主作業は、手元の `vram.bin` を field/town mapchip 型か battle CHR 型かに分類し、次の runtime logging に接続すること。

## 今回の解析結果

- 現在参照できる `vram.bin` は battle CHR 型。
- `0x0000..0x7FFF` は tilemapではなく、4bpp CHR atlas として読むのが自然。
- `0x8000..0xAFFF` はUI/glyph/補助タイル候補が混ざる。
- `0xC000..0xDFFF` もUI/数字/ラベル系候補が残る。
- `0xE000..0xEFFF` はほぼ空き。
- `0xF000..0xFFFF` は少数unique tileのパターン領域。

## GitHub最新状態との接続

GitHub mainでは `tools/lua` に以下のgraphics系Luaが見える。

- `shinmomo_graphics_full_capture_v2_snes9x_bizhawk_20260502.lua`
- `shinmomo_graphics_mapchip_probe_v1_bizhawk_snes9x_20260501.lua`
- `shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua`

このうち、今後の正本は unified polling Lua とし、今回の `analyze_vram_layout_candidates_v1.py` を後段解析器として接続する。

## 次のログ採取指示

次回Lua採取では以下を必ず分離保存する。

```text
session_xxxx/
  frame_099282/vram.bin
  frame_099282/cgram.bin
  frame_099282/oam.bin
  frame_099282/bg_summary.csv
  frame_099282/visible_objects.csv
  frame_100500/vram.bin
  ...
```

同名ファイル上書きは禁止。複数snapshot比較がないと、scroll更新・tilemap更新・CHR転送の区別が鈍る。

## コミット内容

このrun2パックでは、以下を追加する。

- docs/graphics/VRAM_LAYOUT_CLASSIFICATION_20260502_RUN2.md
- docs/handover/SHINMOMO_VOL016_GRAPHICS_CONTINUE_RUN2_20260502.md
- data/csv/current_vram_region_summary_20260502_run2.csv
- data/csv/current_vram_tilemap_candidate_scores_20260502_run2.csv
- graphics/battle/*.png
- tools/python/analyze_vram_layout_candidates_v1.py

## 進捗扱い

- graphics/mapchip reconstruction: 57% -> 60%
- Goal 11: 80%維持。ただしgraphics外部化サブ項目は前進
- Goal 12: 82% -> 83%
- Goal 13: 75%維持。観測基盤のみ前進、本体/patch readinessは別スレッド
