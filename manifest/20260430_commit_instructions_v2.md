# コミット手順案

```bash
unzip shinmomo_vol014_merge_package_v2_20260430.zip
cd shinmomo_vol014_merge_package_v2_20260430

# 既存リポジトリのルートにコピーする場合
rsync -av ./ /path/to/shinmomo/

cd /path/to/shinmomo
git status
git add docs/handover docs/permanent_reference data/rom_anchor_checks scripts/analysis reports reference data/tables data/disassembly
git commit -m "Add vol014 merge handover v2 and weapon special anchors"
```

## 注意

既に同名ファイルがある場合は `git diff` で差分確認してください。
