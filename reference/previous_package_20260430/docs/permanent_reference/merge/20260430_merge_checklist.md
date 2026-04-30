# vol014 マージチェックリスト（2026-04-30）

## コミット前確認

```bash
find . \( -name '*.smc' -o -name '*.sfc' \) -print
```

何も出ないこと。

## マージ順

1. `docs/handover/20260430_vol014_merge_handover.md` を読む。
2. 別スレッドの最新引継ぎと比較。
3. `docs/permanent_reference/weapon_special/20260430_weapon_special_working_hypotheses.md` の仮説を、別スレッド成果で上書きできるか確認。
4. `reference/imported_handover/` の過去資料が既存GitHubにある場合は、重複ファイルの差分だけ確認。
5. CSVは既存ファイルと差分がない場合、無理に再コミットしない。

## Gitコマンド例

```bash
git status
git add docs reference data reports manifest NOT_INCLUDED_ROM.txt README.md
git commit -m "docs: add vol014 merge handover package"
```
