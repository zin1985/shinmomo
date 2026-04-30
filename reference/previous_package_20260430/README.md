# shinmomo vol014 merge package 2026-04-30

このZIPは、新桃太郎伝説解析 vol014 の別スレッド結果とマージしやすいよう、今回スレッドで利用した資料と引継ぎ情報を GitHub コミット可能な構成に整理したものです。

## 重要

- ROM本体 `.smc/.sfc` は含めていません。
- 既存の引継ぎ資料、CSV、逆アセンブルテキスト、今回スレッドの統合引継ぎメモを含めています。
- 今回スレッド内で出た「武器特殊能力サブシステム」系の進展は、静的根拠が未固定のものを含むため `working_hypotheses` として分離しています。
- 他スレッド側の成果とマージする際は、`docs/handover/20260430_vol014_merge_handover.md` を先に読んでください。

## 収録構成

```text
docs/
  handover/
  permanent_reference/
    goals/
    merge/
    weapon_special/
reference/
  imported_handover/
data/
  tables/
  disassembly/
reports/
  thread_summaries/
manifest/
```

## 推奨コミット

```bash
git add docs reference data reports manifest NOT_INCLUDED_ROM.txt README.md
git commit -m "docs: add vol014 merge handover package"
```

## マージ時の注意

- `reference/imported_handover/` は過去資料の保管場所です。既に同名ファイルがGitHub側にある場合は、内容差分を確認してから上書きしてください。
- `data/tables/` のCSVは既存CSVと重複する可能性があります。Git上で差分がない場合はコミット不要です。
- `docs/permanent_reference/weapon_special/20260430_weapon_special_working_hypotheses.md` は「確定資料」ではなく、次の検証タスク用メモです。
```
