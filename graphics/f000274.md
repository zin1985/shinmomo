# 新桃太郎伝説 フィールド マップチップ サンプル出力 2026-05-01

## 生成元

- `shinmomo_field_graphics_analysis_20260501/field_bg_candidate_map0000_char8000_4bpp_64x64.png`
- 仮定: `tilemap base = VRAM 0x0000`, `char base = VRAM 0x8000`, `4bpp`
- 2x2 tiles = 16x16 pixel を仮メタタイル / マップチップとして抽出

## 内容

- `shinmomo_field_mapchip_sample_top16_large.png`
  - 頻出上位16件を大きく並べた確認用
- `shinmomo_field_mapchip_sample_top64.png`
  - 頻出上位64件の一覧
- `chips/*.png`
  - 個別の 16x16 マップチップ候補を 4倍拡大した PNG
- `mapchip_sample_top64_metadata.csv`
  - 2x2 tilemap entry と出現位置、出現回数

## 注意

これは VRAM snapshot からの仮復元です。
パレットはまだ実機CGRAMの正確反映ではなく、既存の白黒/疑似濃淡表示です。
ROM資材から直接復元した完全版ではありません。
