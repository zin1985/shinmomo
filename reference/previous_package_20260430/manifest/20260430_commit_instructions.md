# コミット手順

```bash
unzip shinmomo_vol014_merge_package_20260430.zip -d /tmp/shinmomo_merge
cd /path/to/shinmomo
cp -R /tmp/shinmomo_merge/shinmomo_vol014_merge_package_20260430/* .
find . \( -name '*.smc' -o -name '*.sfc' \) -print
git status
git add docs reference data reports manifest NOT_INCLUDED_ROM.txt README.md
git commit -m "docs: add vol014 merge handover package"
```

## 注意

- ROM本体が検出された場合はコミットしない。
- `reference/imported_handover/` と `data/tables/` は既存GitHub側と重複する可能性があります。
- 重複が多い場合は `docs/handover/` と `docs/permanent_reference/` の新規ファイルだけコミットしてもよいです。
