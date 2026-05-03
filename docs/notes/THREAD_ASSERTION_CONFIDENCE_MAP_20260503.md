# Thread assertion confidence map (2026-05-03)

このファイルは、後半Runで強く表現された内容を、実証度ごとに再分類するためのもの。

## A. 確定・実バイトで確認済み

| 項目 | 確度 | 根拠 |
|---|---|---|
| bank87内に `$0759/$0799` へのstore/readが複数ある | 高 | `bank87_0759_0799_xrefs_vol017.csv` |
| `$87:810D / 8173 / 81DF / 824E` は `$0759/$0799` writer | 高 | 実バイト確認 |
| これら4本は `$87E0/$89E0` 即値初期化系 | 高 | `A9 E0`, `A9 87/89`, `STA $0759/$0799,X` |
| `$87:8459` は `$0759` 0/1 toggle | 高 | `INC; AND #01; STA $0759,X` |
| `$87:E579` はposition/velocity風更新 | 高 | `$0719 += $0799`, `$0759 += $07D9` |
| `$87:E79A` 周辺はsave/restore系 | 高 | `$0377..$0386` とslot間の双方向コピー |
| `0x39850` 付近に9-byte row列と `9A F0` 末尾wordがある | 高 | `macro_9byte_rows_vol017.csv` |

## B. 強い仮説

| 項目 | 確度 | 備考 |
|---|---|---|
| `$87:82C0` はobject-slot pointer reader / mini-interpreter候補 | 中高 | `$0759/$0799 -> $2A/$2B`, `($2A),Y`候補がある |
| F09A/F0DB/F0C6系はtarget-side blob label | 中高 | 9-byte row末尾wordとLoROM labelが整合 |
| `0x39850/39993` は条件/イベント/施設blob側 | 中高 | 過去handoverと整合 |

## C. 作業仮説・未検証

| 項目 | 確度 | 検証方法 |
|---|---|---|
| opcode 0x07 = command dispatch | 低〜中 | `$87:82C0`内部のdispatch実コード特定 |
| Table A = opcode->behavior map | 低 | 実アドレス未発見 |
| command_tableはbank87近傍 | 低〜中 | JMP indirect / pointer table探索 |
| `$0799` はVM対象objectでwait counter | 中 | routine別に確認要。timer用途は確かだが全VM固定は未証明 |
| NPC軽減 = command実行頻度制御 | 中 | OAM/active object runtime logとの照合が必要 |

## D. 撤回・補正

| 旧見立て | 補正後 |
|---|---|
| `$0759/$0799` は全object共通pointer | object type依存の汎用slot field |
| 9-byte row末尾wordが直接 `$0759/$0799` に入る | 直接store証拠なし。blob labelとして読む方が安全 |
| Goal13を `$0759/$0799` 固定で追う | active list -> object type -> routine -> slot meaning の順に追う |
