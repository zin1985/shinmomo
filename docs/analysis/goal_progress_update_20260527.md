# Goal3 / Goal7 / Goal9 解析進捗更新（2026-05-27）

## 目的

ユーザー指定の低進捗領域 Goal3 / Goal7 / Goal9 を、GitHub にそのまま配置できる形で追加解析した。
ROM 本体や raw copyrighted assets は含めない。

## 入力

- ROM: `Shin Momotarou Densetsu (J)_original.smc`
- ROM size: 2,097,152 bytes
- SHA256: `f6a345e2f07f0cbc4eff7d4ff06ae88a814a98fdf100c7bf7351168c73916a98`
- 既存資料: 2026-03-13 / 2026-03-18 handoff、260510Y handoff

## 進捗更新サマリ

| Goal | 旧見立て | 今回更新 | 更新理由 |
|---|---:|---:|---|
| Goal3 | 58% | 60〜62% | `7E:201E..2030` / `7E:3004..303C` への絶対参照候補を機械抽出し、次に読むべき bank/operand を CSV 化した。まだ blind scan のため確定ではなく、伸び幅は控えめ。 |
| Goal7 | 45〜50%相当 | 60〜62% | `0x0B01F9` の equipment-id script-pack pointer table を zero-based entry として読み、230装備に対して hook pack を展開。30件の non-default pack を確定候補として表化した。 |
| Goal9 | 58% | 62〜64% | `0x41A10` 8-byte target table を160件展開し、`0x39850` / `0x39993` anchor と `398xx` 9-byte row series をCSV化。script/data blob 仕様書化の足場が増えた。 |

## 今回作成した成果物

```text
docs/analysis/goal3_wram_struct_progress_20260527.md
docs/analysis/goal7_weapon_special_progress_20260527.md
docs/analysis/goal9_script_spec_progress_20260527.md
docs/analysis/goal_progress_update_20260527.md
data/static/goal3_wram_refs_20260527.csv
data/static/goal3_wram_ref_summary_20260527.csv
data/static/goal7_weapon_script_pack_by_equipment_20260527.csv
data/static/goal7_weapon_hook_targets_20260527.csv
data/static/goal7_hook_body_windows_20260527.csv
data/static/goal9_41a10_target_records_20260527.csv
data/static/goal9_398xx_9byte_rows_20260527.csv
data/static/goal9_script_blob_windows_20260527.csv
tools/python/extract_goal3_goal7_goal9_static.py
```

## 注意

- Goal3 の static scan は opcode-like bytes を拾うため、data area の false positive を含む。
- Goal7 はかなり強い。table entry 0 を dummy/default と見て、装備ID `N` は pointer table entry `N` を使う形が、玄武の刀以降の特殊packと整合する。
- Goal9 は reader 本体発見ではない。今回は target table / target-side blob の仕様書化を進めた。
