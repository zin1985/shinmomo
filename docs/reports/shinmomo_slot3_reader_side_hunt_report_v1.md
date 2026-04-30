# slot3 word reader側 調査 v1

## 結論

`9A F0 / DB F0 / C6 F0...` の **受け側** はかなり見えました。

受け側は `$84:8078` 周辺のscript VM実行ループです。
`$98-$9A` にscript pointerが入ると、そこから `$83:F09A` や `$83:F0DB` の `07 ...` で始まるmini-script / record streamを実行します。

ただし、今回の静的探索では、`0x39850` の9-byte macro row末尾2byte、つまりslot3 wordを直接読んで `$98/$99` に入れる **2byte label reader本体** はまだ確定できていません。

## 今回確認できた制御の受け皿

### `$84:8078` = receiver / script interpreter

`$84:8078` は、script pointer `$98-$9A` を前提に次byteを読み、compact high-byte classまたは通常opcode dispatcherへ流します。

つまり、`$83:F09A` などへ制御が渡った後に実際に読む本体です。

```text
$98-$9A = $83:F09A
  ↓
$84:8078
  ↓
83:F09A: 07 20 01 A0 00 ...
```

この意味では、`$83:F09A / F0DB / F0C6...` の **受け側reader** は `$84:8078` と言えます。

## 見つかったpointer転送候補

### `$84:81F3`

```asm
84:81F3  B7 98       LDA [$98],Y
84:81F5  PHA
84:81F6  INY
84:81F7  LDA [$98],Y
84:81F9  PHA
84:81FA  INY
84:81FB  LDA [$98],Y
84:81FD  STA $9A
84:81FF  PLA
84:8200  STA $99
84:8202  PLA
84:8203  STA $98
84:8207  JMP $8078
```

これは **3byte absolute script pointer** 用です。

slot3は2byteなので、`9A F0` を直接読むreaderではなさそうですが、「制御を `$84:8078` に渡す形」は一致します。

### `$84:848F`

こちらも3byte pointerを読んで `$98-$9A` を差し替え、`$84:8078` に飛びます。
現在pointerを保存しているので、nested call / subscript call系に見えます。

### `$84:8225`

```asm
84:8225  LDA [$98],Y
84:8228  BPL ...
84:822A  CLC
84:822B  ADC $98
84:822D  STA $98
...
```

これは **1byte signed relative branch** です。
slot3の2byte labelとは違います。

## 重要な否定結果

`opcode $10` から呼ばれる `$80:B572` も見ましたが、これはslot3 word reader本命からは後退です。

理由は、`$80:B572` / `$80:B7A7` 周辺は `$1100/$2100/7E:24xx` 系の状態や資材処理を強く触っており、`[$98],Y` から直後の `9A F0` を読む構造ではありませんでした。

つまり、

```text
10 07 9A F0
```

を

```text
opcode10が 07 を読み、さらに 9A F0 をbranch先として読む
```

と見る線は薄くなりました。

## 今の整理

現時点では、この構造が一番安全です。

```text
0x41A10 条件表
  ↓
0x39850 / 0x39993
  ↓
9-byte macro row
  ↓
slot3 = 16bit label word
  ↓
何らかのmacro row evaluatorが $83:xxxx に変換
  ↓
$98-$9A = $83:F09A / $83:F0DB / ...
  ↓
$84:8078 script interpreterが実行
```

つまり、**受け側は `$84:8078` でほぼ見えたが、slot3 wordを `$98-$9A` に積むreaderは未確定**です。

## 次に攻めるべきところ

次は、`9-byte macro row evaluator` そのものを探す必要があります。

探す条件は以下です。

```text
1. 0x41A10 table targetを受け取る
2. 0x39850 / 0x39993 を入力にする
3. 9-byte rowの末尾2byteを読む
4. そのwordを同bank $83 のscript labelとして扱う
5. $98/$99/$9Aへ反映、または $84:8078相当へ渡す
```

具体的には、次の検索が有効です。

```text
- 0x41A10 table reader本体
- 8byte record targetを展開して $83:9850 等へ変換する箇所
- $83:F09A/F0DB へ直接ではなく、row末尾wordを汎用的に使う処理
- $98/$99/$9Aを書き換える処理のうち、3byte absoluteでも1byte relativeでもないもの
```

## 今回の進み

- `$83:F09A/F0DB/F0C6...` の実行受け側が `$84:8078` VM loopであることを確認
- `$84:81F3` / `$84:848F` / `$84:8225` のpointer transfer系を整理
- `opcode10 -> $80:B572` がslot3 word reader本命ではないことを確認
- 残る本丸は `9-byte macro row evaluator` と切り分け
