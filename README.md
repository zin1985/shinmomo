# shinmomo vol013 merge commit package

新桃太郎伝説解析 vol013 の別スレッドマージ用パッケージです。

## 最初に読むファイル

1. `docs/handover/SHINMOMO_VOL013_MERGE_HANDOVER_20260430.md`
2. `docs/handover/shinmomo_lorom_addressing_correction_note_v1.md`
3. `docs/handover/GOAL_PROGRESS_VOL013_20260430.csv`
4. `manifest/MANIFEST.csv`

## 重要

ROM本体は含めていません。  
過去成果物にはHiROM風の旧CPUラベルが一部残っています。マージ時は **file PCを正** とし、LoROM補正表で読み替えてください。

## 構成

```text
docs/handover/   引継ぎ・アドレス補正・進捗
docs/reports/    解析レポート
docs/notes/      補足メモ
docs/hexdumps/   disasm / hexdump / dump系テキスト
data/csv/         解析CSV
tools/lua/        Snes9x Lua
tools/python/     Pythonダンパ/補助スクリプト
graphics/         raw graphics probe PNGなど
archive/          過去ZIPの展開済み個別ファイル
manifest/         ファイル一覧・除外一覧
```
