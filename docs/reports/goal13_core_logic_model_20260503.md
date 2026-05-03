# Goal13本体側モデル差分（2026-05-03）

## 前提

グラフィック側スレッドでは OAM/VRAM/DMA/BG runtime logging を担当。
このスレッドでは、その観測結果を受けて、NPC/object処理本体へ接続する。

## 重要な補正

`$0759/$0799` は多義的であるため、Goal13で一律pointerとして読むのは危険。

安全な追跡順:

```text
$0A61 active object list
  -> object slot index
  -> object type / routine
  -> そのroutineでの $0619/$0719/$0759/$0799 の意味
  -> OAM submit / VM reader / 通常物理更新
```

## 現時点のGoal13進捗扱い

- 統合管理値: 75〜78%相当
- グラフィック観測基盤込みなら高い
- 本体安定パッチreadyではない

## 次の検証ポイント

```text
C0:B100
B294 table
$0A61 active linked list
$0A1C / $0B27
$87:82C0 caller / object type
```

## パッチ方針

現時点で直接 `$0A61` active list を壊すpatchは危険。
比較的安全なのは、OAM submit / command実行頻度 / wait値調整を実測後に触ること。
