# 0x41A10 -> 0x39850 / 0x39993 静的分解メモ v1

## 結論

`0x39847..0x39A74` は、少なくとも先頭 `0x12E` bytes が **9バイト固定長の条件分岐レコード列** としてかなりきれいに割れる。

暫定フォーマット:

```text
byte0  predicate / 条件命令ID
byte1  operand A
byte2  operand B
byte3  selector / 対象index
byte4  value_kind / 参照・比較種別
byte5  arg_lo
byte6  arg_hi      ; little endian 16bit arg
byte7  target_lo
byte8  target_hi   ; little endian 16bit branch target, abs = 0x30000 + target
```

つまり、ここは普通の可変長script本文というより、**条件レコードを9バイト単位で走査し、合致したら末尾2バイトのtargetへ飛ぶ表** と見るのが自然。

## 41A10側との接続

- `0x41C30` record: `74 01 03 02 05 04 50 98` -> `0x39850`
- `0x41D68` record: `00 05 03 02 02 02 93 99` -> `0x39993`

`0x39850` は A系レコード列の **row1** 先頭。
`0x39993` は B系 row14 の末尾 `F0` に着地しており、実効開始は `0x39994` の可能性が高い。これは reader が開始時に1バイト進める、または直前target_hiをラベルとして持つ特殊な入り方の可能性がある。

## ブロック分割

```text
0x39847..0x39915 : A系 23 records。共通branch target = 0x3F09A
0x39916..0x399E4 : B系 23 records。先頭20 recordsは共通branch target = 0x3F0DB
0x399E5..0x39A74 : 後続混成 16 records。各recordごとにtargetが散る
0x39A75..        : 65816コードらしき領域に切り替わる（DA AA CE 51 11... RTSあり）
```

## A/Bペアの強い法則

A系とB系の同indexを比べると、基本的に:

```text
selector は同じ
arg_B = arg_A + 1
A target = 0x3F09A
B target = 0x3F0DB（ただし後半3件は C6/CD/D4 F0）
```

これは `A/B = 下限/上限`、または `現在値に対する範囲分岐` のような構造を疑わせる。

## 39993問題

`0x39993` の周辺:

```text
0x3998B: 38 05 01 12 32 9d 2b db f0
0x39994: 38 05 01 10 32 8b 27 db f0 38 05 01 0f 32 82 25 db f0 38 05 01 11 32 94 29 db f0
```

`0x39993` は `38 05 01 12 32 9D 2B DB F0` の最後の `F0`。
次バイト `0x39994` からは `38 05 01 10 32 8B 27 DB F0` が始まる。
そのため `0x41A10` の target は、厳密なレコード先頭ではなく **reader都合の入口ラベル** である可能性が高い。

## 代表的な命令ファミリ

| b0 | 件数 | 暫定意味 |
|---|---:|---|
| `38` | 43 | 条件predicate候補 |
| `0B` | 7 | 条件predicate候補 |
| `10` | 4 | 条件predicate候補 |
| `37` | 3 | 条件predicate候補 |
| `2C` | 3 | 条件predicate候補 |
| `0C` | 1 | 条件predicate候補 |
| `02` | 1 | 条件predicate候補 |


| b4 | 件数 | 暫定意味 |
|---|---:|---|
| `32` | 38 | value_kind候補 |
| `35` | 9 | value_kind候補 |
| `37` | 5 | value_kind候補 |
| `31` | 4 | value_kind候補 |
| `33` | 3 | value_kind候補 |
| `17` | 1 | value_kind候補 |
| `30` | 1 | value_kind候補 |
| `07` | 1 | value_kind候補 |


## 出力CSV

- `records_39847_39A75_split_9byte.csv`: 9バイト単位の全レコード
- `AB_pair_analysis_39847_399E5.csv`: A/B対応表
- `record_family_counts.csv`: b0 / b4 / branch target の集計

## 次に詰める点

1. 9バイトrecord reader本体を探す。条件は `+8/+9` で進むループ、末尾2バイトtargetを読む、b0ごとのpredicate dispatch。
2. `0x39993` がなぜ `target_hi` に入るのかをreader側で確認する。
3. `b0=38/37/0B/10/2C/02/0C` のpredicate意味を、他の `0x41A10` target blobにも横展開して推定する。
4. branch target `0x3F09A / 0x3F0DB / 0x3F0C6 / 0x3F0CD / 0x3F0D4` の先をscript命令単位に割る。
