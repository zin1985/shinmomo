# 新桃太郎伝説 opcode 0x02 family / $9BEE table 分解 v1

## 結論

`opcode 0x02` は、直後1バイトを subcode として読み、`89:9BEE + (subcode - 1) * 3` から24bitポインタを取得する。

ただし、これは単純な「CPU subhandler 関数表」ではなく、`$2A-$2C` に積んだ24bitポインタを `JSL $84:89C7` に渡す構造に見える。
そのため、現時点では **subhandler table** というより **subresource / subscript pointer table** と呼ぶ方が安全。

## opcode 02 handler

```asm
89:89A5  LDA [$98],Y
89:89A7  REP #$30
89:89A9  AND #$00FF
89:89AC  DEC A
89:89AD  STA $00
89:89AF  ASL A
89:89B0  ADC $00
89:89B2  TAX
89:89B3  LDA $9BEE,X
89:89B6  STA $2A
89:89B8  LDA $9BEF,X
89:89BB  STA $2B
89:89BD  SEP #$30
89:89BF  JSR $895E
89:89C2  JSL $84:89C7
89:89C6  RTS
```

## 0x39847..0x399E5 で実際に使われる subcode

| subcode | 使用回数 | table target | 分類メモ | target先頭16バイト |
|---:|---:|---|---|---|
| `32` | 2 | `85:990C` | `data_or_vm_stream_like` | `23 87 84 AD 85 19 D0 2B 20 00 9C AE 86 19 BD D5` |

## 旧9バイトrecord解釈の修正

前回までの `0x39847..0x399E5 = 9バイト固定record` という見方は、観察上は便利だが、実装上のreaderとは少し違う。

実装としては、

```text
38 <lo> <hi> 02 <subcode> <tail operands...>
```

というVM命令マクロが9バイト周期で並んでいる可能性が高い。

特に `02 <subcode>` の後続tailは、opcode02本体ではなく、`JSL $84:89C7` または `$9BEE` table target側が読む可能性が高い。

## 重要な修正点

- `$9BEE` は `opcode 02` handlerから直接参照される。
- `$9BEE` entryは3バイト long pointer。
- `subcode 0x32` は `85:990C` を指し、0x398xx主系統で最も多く使われる。
- `subcode 0x35` は `84:A2B7`、`0x37` は `81:E938` を指す。
- `0x37` と `0x30` は先頭が `FF` 埋め領域に見えるため、未使用/特殊/未到達の可能性がある。
- `0x39993` の9バイト境界ズレは、固定record readerではなくVM bytecode streamとして見ると不自然さが下がる。

## 次に攻める場所

1. `JSL $84:89C7` の正体確認
2. `$2A-$2C` が `$84:89C7` 内または下流でどう使われるか追跡
3. `subcode 0x32 -> 85:990C` の stream/処理仕様を分解
4. `02 32 10 07 9A F0` の tail 4 bytes が比較値・branch先・引数のどれかを確定
5. `0x39850` と `0x39994` の入口差分をVM stream単位で再パース

## 出力ファイル

- `shinmomo_opcode02_9BEE_subtable_v1.csv`
- `shinmomo_opcode02_9BEE_used_by_398xx_v1.csv`
- `shinmomo_39847_399E5_rows_opcode02_macro_parse_v1.csv`
- `shinmomo_opcode02_handler_and_9BEE_notes_v1.txt`
