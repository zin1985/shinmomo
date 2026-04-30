# 新桃太郎伝説 グラフィック調査 v1

## 実行内容

- ROMサイズ: 2,097,152 bytes
- 2bpp/4bpp raw tile scan window: 0x1000 bytes step
- full raw sheets: 出力済み
- candidate CSV: `shinmomo_graphics_window_scores_v1.csv`

## フォルダ

- `01_full_raw_2bpp_sheets/`: ROM全域を2bpp raw tile sheet化
- `01_full_raw_4bpp_sheets/`: ROM全域を4bpp raw tile sheet化
- `02_font_candidates/`: フォント候補
- `03_face_person_candidates/`: 顔グラ/人物グラ候補
- `04_mapchip_candidates/`: マップチップ候補
- `05_known_reference_regions/`: 既知アドレス周辺の参考出力
- `06_da3800_decoded_stream_views/`: 既存DA:3800 decoded CSVからの小資材ビュー

## 注意

これは「生ROMをSNES tile形式として可視化する探索器」です。
圧縮グラフィックはこの方法だけでは正しく出ません。
見た目どおりに復元するには、Snes9xでVRAM/CGRAM/tilemap/OAMを実行時dumpし、CGRAM paletteとtilemap属性を適用してください。

## アドレス表記

ファイル名にはPC offsetとLoROM想定SNESアドレスを併記しています。
例: `pc026A60_84_EA60` はPC `0x026A60` / LoROM `84:EA60` 相当です。
