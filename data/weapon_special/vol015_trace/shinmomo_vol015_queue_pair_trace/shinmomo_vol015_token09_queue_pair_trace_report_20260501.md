# 新桃太郎伝説 vol015: token09 queue pair 逆追跡メモ（2026-05-01）

## 対象

- `C7:9EA5`
- `C7:9EC3`
- `C7:A566`
- `C7:A57D`

これらは前回、weapon descriptor index `0x16` の corrected record head として抽出した `token 09` 地点。

## 結論

4地点の先頭 `09` は、いずれも **C7 stream内の直後バイトを operand として消費しない**。

実際には:

```text
token 09
  -> 89:9F24
  -> JSR 89:9EC7
  -> queue[$1296_before] を pop
  -> A = $1297[$1296_before]
  -> X = $129F[$1296_before]
  -> $1296++
```

したがって、4地点の先頭 `09` が消費する queue pair は静的には以下で表すのが正確。

```text
(value,type) = ($1297[$1296_before], $129F[$1296_before])
```

この `(value,type)` の実値は、C7 stream側ではなく、事前に `85:9F4B` が `$19D5/$19E5/$19F5/$19C5` から作った queue 内容に依存する。

## `85:9F4B` から見た queue pair 生成則

### case A: `$19E5[$1986] == 0`

```text
pair0 = (value=$19D5[$1986], type=0x04)
terminator = (0,0)
```

### case B: `$19E5[$1986] != 0`

まず:

```text
pair0.type = 0x06
pair0.value = $19D5[$1986]
```

ただし:

```text
if ($19C5[$1986] & 0x10) != 0:
    pair0.value = 0x48
```

その後:

```text
if pair0.value < 0xDB:
    pair1 = (value=$19F5[$1986], type=0x0F)
    terminator = (0,0)
else:
    terminator = (0,0)
```

## 4地点の判定

| C7 addr | 先頭byte | 消費するqueue |
|---|---:|---|
| C7:9EA5 | 09 | queue[$1296_before] |
| C7:9EC3 | 09 | queue[$1296_before] |
| C7:A566 | 09 | queue[$1296_before] |
| C7:A57D | 09 | queue[$1296_before] |

つまり、この4地点は **別々の固定pairを持つのではなく、同じ queue pop 命令 `09` として、runtime queue head の pair を消費する**。

## 重要な認識更新

前回までの「token09 = 直接能力ID」説は撤回。

正しくは:

```text
token09 = runtime queue-driven family resolver trigger
```

weapon側で見ると:

```text
weapon descriptor corrected record head
  -> token09
  -> queue pair をpop
  -> AE3A / fallback family resolver に渡す
```

## 次に攻める箇所

次は `$19D5/$19E5/$19F5/$19C5` の値を、weapon特殊能力実行直前にどこで立てているかを見る。

候補:

```text
85:90A3 / 92AF / 93AC / 93BC / 9470 / 957F
19D5/19E5/19F5/19C5 staging writer 群
```

ここを取れれば、玄武/白虎/朱雀/青龍/酒呑/凪モリ/包丁系が、実際にどの `(value,type)` を投げているかまで確定できる。
