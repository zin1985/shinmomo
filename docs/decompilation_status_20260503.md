# Decompilation status 2026-05-03

## できたこと

- 既知テーブルをC99構造体へ変換。
- VM/AI/time slicing仮説をCランタイム骨格へ変換。
- ROMから既知範囲を再抽出するPythonツールを追加。
- `make` でホスト環境向けに再コンパイルできる。

## できていないこと

- ROM全体の完全な逆コンパイル。
- SNES実機/エミュレータで動くROM再生成。
- すべての65816 codeのC移植。
- 全イベントscriptの完全復元。

## 生成数

- item records: 165
- equipment records: 234
- branch records: 160
- macro A rows: 64
- macro B rows: 64
