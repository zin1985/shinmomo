# 新桃太郎伝説 vol015 静的解析メモ: token09 実行時の $1986 と queue build 経路

## 結論

`weapon descriptor` の `token09` が消費する queue pair は、C7 descriptor そのものから固定的に決まるのではなく、直前に `85:9F4B/9F94/9F9B` 系で `$1297/$129F` に構築された queue から `89:9EC7` が pop する。

今回の静的解析で重要なのは、`85:9F4B` の唯一の直接 JSR 呼び出しが `85:80B7` にあること。

```asm
85:80B7  LDA [$98],Y
85:80B9  TAX
85:80BA  JSR $9F4B
85:80BD  JSL $84:9BC5
85:80C1  RTS
```

このため、少なくともこの経路では、

```text
queue write index = mini-VM stream operand
row source        = $1986
queue builder     = 85:9F4B
evaluator         = 84:9BC5 -> 84:8410 系
```

と読める。

## $1986 の静的な意味

`$1986` は「weapon descriptor 内で固定された値」ではなく、bank85 側 staging row の current selector。

今回改めて見た `85:9FA9` scan loop は、`$198D=0..0F` を走査し、非空 `$19D5[row]` を見つけるたびに

```asm
85:9FB7  STX $1986
```

で current row として選ぶ。ただし、この loop 内には `JSR $9F4B` は無い。したがって `85:9FA9` は queue builder 本体ではなく、row scheduler/materializer と見るのが安全。

## queue builder entry の3形態

```asm
85:9F4B  Y = $1986
85:9F94  Y = $198B
85:9F9B  Y = A
```

共通本体は `85:9F50` 以降。

つまり token09 用 queue は、次の3種類の row source から作れる。

| entry | row source | 意味 |
|---|---|---|
| `85:9F4B` | `$1986` | current staging row。`85:80B7` から直接呼ばれる本命 |
| `85:9F94` | `$198B` | current choice/current row 系 |
| `85:9F9B` | `A` | explicit row index 引数 |

## 85:9FA9 scan loop の位置づけ

`85:9FA9` は下記の処理を行う。

```text
$198D = 0
$19BB = 0
while $198D < 0x10:
    X = $198D
    if $19D5[X] != 0:
        $1986 = X
        compare $19E5[X] with $0619[current object]
        schedule/materialize via $80ADBF
        $0619[current object] = $19E5[X]
    $198D++
```

このため、runtime 上は「直前に scan loop が選んだ row」が `$1986` に残り、それを `85:80B7 -> 9F4B` が queue 化する可能性が高い。ただし静的には、`85:80B7` 直前に別 setter が `$1986` を更新する可能性も残る。

## 今回の静的な絞り込み

最も強い候補は以下。

```text
85:93AC 系で expanded row を構築
  -> $19D5/$19E5/$19F5/$19C5 を埋める
  -> 85:9FA9 scan loop が非空 row として拾い $1986 にセット
  -> 85:80B7 mini-VM command が stream operandをXにして 9F4B
  -> $1297/$129F queue構築
  -> 84:9BC5 evaluator
  -> C7 descriptor token09
  -> 89:9EC7 が queue pairをpop
```

## 前回からの補正

前回は `85:9FA9` scan loop が token09 直前の本命のように見ていたが、より正確にはこう。

```text
85:9FA9 = $1986 を選ぶ/更新する scheduler 側
85:9F4B = $1986 row を queue pair に変換する本体
85:80B7 = 9F4B を直接呼ぶ mini-VM command
```

## 次の静的解析候補

1. `85:80B7` が bank85 handler table のどの opcode/index に対応するかを確定する。
2. `84:9BC5 -> 84:8410` が `$12B4/$12B5` descriptor evaluator をどう起動するかを切る。
3. `85:9FA9` を呼ぶ dispatch/table entry を pointer table から特定する。
4. `85:93AC` 系 row と `85:80B7` command が同一シナリオ内で隣接する script stream 例を探す。

## 進捗更新案

- Goal 7: 97% -> 97.5%
- Goal 9: 80% -> 81%
