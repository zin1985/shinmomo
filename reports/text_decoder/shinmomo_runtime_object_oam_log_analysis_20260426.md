# 新桃太郎伝説 runtime object/OAM polling log 解析メモ（2026-04-26）

## 入力ログ

- source: `貼り付けられたテキスト（1 点）.txt`
- TRACE_OBJ_OAM lines: 205
- frame range: 48359..49453
- observed duration: 1094 frames

## 1. 結論

今回のログは、月の神殿の見えているNPC/イベントspriteが `$1569` 系ではなく、`$0A61` active chain と `$0B25/$0AE5/$0BA5/$0C65` 系object workからOAMへ出ていることを強く示す。

`logical_1569` は全ログで以下のまま固定。

```text
01 00 00 00 00 00 00 00 00 00
```

一方、`active_0A61` は全ログで以下の形。

```text
05 FF 0C 02 03 06 07 08 09 0A 0B 04 0D 0E 0F 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

これを `$0A61[index] = next` の linked list と読むと、active chain は以下になる。

```text
05 -> 06 -> 07 -> 08 -> 09 -> 0A -> 0B -> 04 -> 03 -> 02 -> 0C -> 0D -> 0E -> 0F -> 01 -> FF
```

つまり `$0A61` は raw active ID配列ではなく、**next pointer table / active linked list** と見るべき。

## 2. 表示中spriteに対応する主なslot

代表的な表示slotは以下。

| slot | b25 | ae5 | x | y | 解釈 |
|---|---|---|---|---|---|
| s02 | 22 | 07/08 | 00:70 | 00:7F | 下側中央キャラ。2 OAM piece候補 |
| s0C | 23 | 37/38 | 00:70 | 00:6F | 中央上寄りキャラ/部品 |
| s0D | 23 | 5A/5B | 00:70 | 00:5F | 中央奥キャラ/部品 |
| s0E | 23 | 4A/4B | 00:60 | 00:5F | 左側キャラ |
| s0F | 23 | 63/64 | 00:80 | 00:5F | 右側キャラ |

s03..s09 は `b25=20` でactive chain上に存在するが、`ae5=00` のためOAMには出ていない待機/不可視slot候補。

## 3. OAM mirror

代表OAM head:

```text
78 6F 08 62 70 6E 02 62 70 5E 4A 22 70 4E 62 62 60 4E 80 62 80 4E 88 62 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00 00 E0 00 00
```

4byte単位で見ると、先頭6 sprite piece が実表示で、その後は `Y=E0` で隠されている。

```text
78 6F 08 62
70 6E 02 62
70 5E 4A 22
70 4E 62 62
60 4E 80 62
80 4E 88 62
00 E0 00 00 ...
```

これは過去の「stale OAMをY=E0で隠す」仮説と一致する。

## 4. 重要な認識更新

### 修正前

```text
$1569 logical object list がNPC大量表示の本線
```

### 修正後

```text
$1569 はscript/event logical actor系
月の神殿の画面上NPC/イベントspriteは $0A61 active chain + object work + OAM mirror が本線
```

NPC大量表示軽減の本線は二層に分けるべき。

```text
A. script/event logical actor層
   $195E/$1958 -> C1:9474 -> $1569

B. map/cutscene visible object層
   $0A61 active linked list
   -> $0B25/$0AE5/$0E27/$0BA5/$0C65
   -> OAM builder
   -> $0EE9 OAM mirror
```

## 5. Goal 13進捗補正

今回のログで `$0A61` active chain本線が実測できたため、Goal 13は **90% -> 94%** に再上げしてよい。

ただし、以前の **98%** は `$1569` 系に寄せすぎていたため、まだ戻さない。

残りは以下。

1. `$0A61` active chainを構築するwriterを静的に逆引きする
2. s02/s0C/s0D/s0E/s0F の生成元を特定する
3. `b25=22/23` のgroup意味をB294 sprite groupと照合する
4. `ae5=07/08,37/38,5A/5B,4A/4B,63/64` をB294 frame定義へ引く
5. OAM piece countと `$0A1C` の関係をもう一段確認する
