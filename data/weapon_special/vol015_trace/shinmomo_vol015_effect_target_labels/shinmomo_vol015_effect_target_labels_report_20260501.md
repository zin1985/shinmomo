# 新桃太郎伝説解析 vol015: CB effect target label refinement (2026-05-01)

## Scope
- CB:1AA4, CB:1A67, CB:18DA を切り、前段の `50 00` scripts から実効果寄りラベルへ寄せた。

## Main result

| target | source | refined label | confidence |
|---|---|---|---|
| CB:1AA4 | 玄武の刀 C1 (`CB:04B8`) | 玄武の刀 使用効果: 使用者の守備力上昇系 | high |
| CB:1A67 | 白虎の刀 C1 (`CB:04EE`) | 白虎の刀 使用効果: 使用者の攻撃力上昇系 | high |
| CB:18DA | 鹿角の錫杖 C8 (`CB:0E08`) | 鹿角の錫杖 proc: 鹿角術型 敵全体会心一撃系 | medium-high |

## Important correction
`CB:1AA4` and `CB:1A67` are not single flat effect bodies. They are nested script packs with a header and hook table.

- `CB:1A67` header: `8F 01 62 8B 19 02 E0 8E B0`
  - `84 -> CB:1A83`, `83 -> CB:1A89` both expose `A4 3C`
  - outer source `CB:04EE` uses `A4 05` then `A0 67 1A CB`
- `CB:1AA4` header: `8F 01 62 8B 19 06 E0 8E B0`
  - `84 -> CB:1AC0`, `83 -> CB:1AC6` both expose `A4 3D`
  - outer source `CB:04B8` uses `A4 03` then `A0 A4 1A CB`

`CB:18DA` is different. It is reached by `CB:0E08` via `B1 DA 18 CB` after `A4 21 -> 50 00 -> A4 22`, and behaves like a direct effect body for 鹿角系.

## Label reasoning
- External equipment data labels 玄武の刀 as a use effect that raises the user's defense, and 白虎の刀 as a use effect that raises the user's attack.
- The ROM-side sibling structure supports this split: 白虎 uses nested pack `CB:1A67` and descriptor `A4 3C`; 玄武 uses nested pack `CB:1AA4` and descriptor `A4 3D`.
- External skill data labels 鹿角 as hitting all enemies with critical strikes; equipment data labels 鹿角の錫杖 as triggering 鹿角. The ROM-side `CB:0E08 -> CB:18DA` path is therefore best named as 鹿角術型 proc.

## Files
- `effect_target_label_candidates_20260501.csv`
- `effect_target_code_slices_20260501.csv`
- `nested_pack_structure_20260501.csv`
