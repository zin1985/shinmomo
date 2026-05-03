# Goal13 NPC throttling model

本スレッド側の担当は、描画ログではなくNPC処理軽減本体のモデル化。

暫定モデル:
```text
active && state allows VM && wait == 0 -> command/script step
```

実コードとしては `$0A61 active list`, `C0:B100`, `B294`, `$0A1C`, `$0B27` との接続を今後詰める。
