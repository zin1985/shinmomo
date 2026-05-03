# shinmomo vol017 thread diff package (2026-05-03)

このパッケージは、前回の別スレッド統合・マージ済みコミット後に、このスレッドで進めた差分だけをまとめたものです。

## 目的

- グラフィック復元系は別スレッド担当として除外
- こちらの担当である script / VM / event / NPC behavior pointer / Goal13本体側の追加解析を整理
- ROM本体、旧ZIP、展開済み大容量素材は含めない

## 最初に読むファイル

1. `docs/handover/SHINMOMO_VOL017_THREAD_DIFF_HANDOVER_20260503.md`
2. `docs/notes/THREAD_ASSERTION_CONFIDENCE_MAP_20260503.md`
3. `docs/handover/GOAL_PROGRESS_VOL017_THREAD_DIFF_20260503.csv`
4. `docs/notes/NEXT_TASKS_VOL017_20260503.md`
5. `manifest/MANIFEST_VOL017_THREAD_DIFF_20260503.csv`

## 重要な補正

Run後半ではVM/AI/command_tableについて強いモデル化を行ったが、実データで未検証のものも多い。
このため、本パッケージでは **確定 / 強い仮説 / 作業仮説 / 撤回・補正** を明確に分けた。

特に、`$0759/$0799` は全object共通pointerではなく、object type依存の汎用slot fieldとして扱う。

## 除外

- ROM本体: `*.smc`, `*.sfc`, `*.fig`, `*.swc`
- 旧ZIP、ZIP内ZIP
- graphics PNG dump / mapchip dump / OAM dump本体

