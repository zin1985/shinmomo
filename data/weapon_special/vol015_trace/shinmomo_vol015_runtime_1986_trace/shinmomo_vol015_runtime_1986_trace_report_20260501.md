# 新桃太郎伝説 vol015 runtime $1986 trace（2026-05-01）

## 目的

weapon descriptor の `token09` 実行時に、`$1986` がどの staging row を指しているかを runtime 前提で絞る。

## 前提

- `token09` は stream 直後の即値を読む命令ではなく、`89:9F24 -> 89:9EC7` で queue pair を pop する。
- queue pair は `85:9F4B` が `$1986` で選んだ staging row から作る。
- したがって、真に追うべき値は「`token09` そのもの」ではなく、`85:9F4B` 実行直前の `$1986`。

## 結論

`token09` 実行時に消費される queue pair は、静的には次で決まる。

```text
row = $1986 at 85:9F4B execution
pair = row[$19D5/$19E5/$19F5/$19C5] -> $1297/$129F
token09 -> 89:9EC7 pop
```

runtime 前提で一番近い selector は、`85:9FAF..A007` の per-row scan loop。

```text
85:9FA9  STZ $198D
85:9FAF  LDX $198D
85:9FB2  LDA $19D5,X
85:9FB5  BEQ skip_empty
85:9FB7  STX $1986   ; current runtime staging row
...
85:A007  INC $198D
```

したがって、weapon descriptor の `token09` 実行時に `$1986` が指しているのは、基本的に以下。

```text
$1986 = $198D scan loop が選んだ「現在の非空 staging row」
```

## もっとも本命の row 起源

weapon special 系としては、`85:93AC` が作る expanded row が本命。

```text
85:93AE  JSR $9535      ; free row search
85:93B6  STX $1986      ; newly allocated row
85:93BC  STA $19D5,X    ; value source = $198E
85:93D3  STA $19E5,X    ; child/phase = $198C
85:93EE  STA $19F5,X    ; occurrence/phase allocator result
```

この row は `85:9F4B` で以下に変換される。

```text
$19E5 != 0:
  pair0 = ($19D5, 06)
  pair1 = ($19F5, 0F)  ; 条件により追加
```

このため、weapon descriptor の `token09` が type06 / type0F 系 resolver と噛み合う場合、`$1986` は `85:93AC` で作られた expanded row を指している可能性が最も高い。

## type04 row も候補ではある

`85:9219..923A` と `85:9286..9297` も `$1986` を立てる。

```text
85:9237  STX $1986
85:9294  STX $1986
```

ただしこれらは `85:9250` により `$19E5=0` の base/type04 row になるため、weapon特殊能力の主線としては一段弱い。

```text
$19E5 == 0:
  pair0 = ($19D5, 04)
```

## 今回の絞り込み結果

| 優先 | `$1986` setter | 解釈 | weapon token09 との関係 |
|---|---|---|---|
| A | `85:9FB7 STX $1986` | runtime scan loop の current row selector | token09直前文脈として最有力 |
| B | `85:93B6 STX $1986` | expanded row builder | weapon type06/type0F の本命 row 起源 |
| C | `85:9237 STX $1986` | type04 base row builder | 補助候補 |
| C | `85:9294 STX $1986` | type04 current `$198E` row builder | 補助候補 |
| restore | `85:9318 STA $1986` | temporary build 後の row restore | `$1986` が volatile cursor である証拠 |

## 次に確定する方法

BizHawk Lua で以下を同時ログするのが最短。

```lua
-- break/log target
85:9F4B  -- queue builder entry
89:9F24  -- token09 handler
89:9EC7  -- queue pop
85:9FB7  -- runtime row selector
85:93B6  -- expanded row allocation
```

ログ項目:

```text
PC
$1986
$198D
$19D5[$1986]
$19E5[$1986]
$19F5[$1986]
$19C5[$1986]
$1296
$1297[0..15]
$129F[0..15]
$12B4/$12B5
current C7 cursor
```

## 進捗更新案

```text
Goal 7 武器特殊能力サブシステム:
96% -> 97%

Goal 9 script仕様書化:
79% -> 80%
```
