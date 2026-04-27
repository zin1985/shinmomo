# 新桃太郎伝説 会話reader静的解析 C9:9DE5 / C9:9E10 / C9:9E57

## 結論

現在の `$12B2/$12C4` ログは、原文そのものではなく **表示直前の作業窓** を拾っている。  
そのため、かな1文字は拾えるが、辞書語・漢字・熟語が欠落しやすい。

原文readerは以下。

```asm
C9:9E57  LDA [$B1]
C9:9E59  INC $B1
C9:9E5D  INC $B2
C9:9E61  INC $B3
```

`$B1/$B2/$B3` が24bit source pointer。

## 主なroutine

| routine | 役割 |
|---|---|
| `C9:9DD2` | text reader state reset。`$1274/$12A8/$1272` などをclear |
| `C9:9DE5` | next display token reader。`$12B2/$12B3` へ出す |
| `C9:9E03` | `0x18..0x1F` 漢字prefix判定 |
| `C9:9E10` | main source reader / control dispatcher |
| `C9:9E34` | source mode別 read entry |
| `C9:9E57` | raw source byte read from `[$B1]` |
| `C9:9E64` | nested source context pop from `$1275..` stack |
| `C9:9F34` | `0x02 xx` dict token handler |
| `C9:9F8D` | source context push to `$1275..` stack |

## 重要なWRAM

| WRAM | 意味 |
|---|---|
| `$B1/$B2/$B3` | 原文source pointer 24bit |
| `$12AA` | source mode / reader mode |
| `$12A9` | text table id |
| `$12B2` | 表示用 current token/glyph low |
| `$12B3` | 漢字prefix時の補助byte |
| `$1274` | nested source context stack depth |
| `$1275/$1277/$1279` | stacked source pointer low/high/bank |
| `$127B` | stacked source mode |
| `$127D` | stacked table id |

## 欠落文字への対策

`桃太郎`、`銀次`、`刀`、`鬼`、`穴`、`体`、`無理` などは `$12B2/$12C4` に必ず出るとは限らない。  
今後は v17 の `src_decode=` を優先し、`$B1/$B2/$B3` が指す原文token列から拾う。
