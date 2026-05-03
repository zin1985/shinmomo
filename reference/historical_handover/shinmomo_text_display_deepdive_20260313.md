# 新桃太郎伝説 文字コード・表示系 深掘りメモ（2026-03-13）

## 今回の大きい発見
今回いちばん大きいのは、**`82:FD67` が「汎用 field 抽出器」だとほぼ確定した**ことです。
これにより、表示VMや `4F` 命令で使われる **selector 0/1/2/3 のスキーマ表** を実体付きで読めるようになりました。

## `82:FD67` の実体
raw `0x02FD67` に実コードあり。

### 入口でやっていること
- `$1FC7` = field番号
- `field * 3 + 3` で **3バイト descriptor** を引く
- descriptor を
  - `$1FCB` = field offset
  - `$1FCC` = field type
  - `$1FCD` = mask / 追加制御
  に展開
- schema 先頭の
  - `+0..1` = base pointer low word
  - `+2` = record size
  を使う
- `80:C11A` で **record_id × record_size** を計算
- base + record_offset + field_offset を作って field を読む
- 結果は `$1FC8..` に返る

### field type
- type 0 = `u8`
- type 1 = `u16`
- type 2 = `u16 + u8`
- type 3 = `bitfield_extract`
  - まず byte を読む
  - mask の最下位1bit位置まで右シフト
  - mask 後の値を返す

## wrapper 群
### `80:DEFB`
- 商品系 wrapper
- schema = `C4:06BE`
- `4F selector 1` の実体と一致

### `80:DF2C`
- キャラ系 wrapper
- schema = `C4:7BF9`
- `81:DAC9` から使用される

### `81:CDCE`
- 装備系 wrapper
- schema = `C4:0000`
- `$1923` を base record id として使用

### `82:FE0D`
- 一覧/基本表示系 wrapper
- schema = `C4:06D6`
- field >= 8 に対して gate がある

## schema 実体
### selector 1 / 商品系
- schema ROM = `0x406BE`
- base = `C4:42AC`
- record size = `11`
- fields:
  - 0: off 0 type u16
  - 1: off 2 type u16
  - 2: off 4 type u16
  - 3: off 6 type u16
  - 4: off 8 type u8
  - 5: off 9 type u8
  - 6: off 10 type u8

### selector 2 / 装備系
- schema ROM = `0x40000`
- base = `C4:49C3`
- record size = `16`
- 少なくとも fields 0..9 がある
  - 0: off 0 type u16
  - 1: off 2 type u16
  - 2: off 4 type u16
  - 3: off 6 type u16
  - 4: off 8 type u8
  - 5: off 9 type u8
  - 6: off 10 type u8
  - 7: off 11 type u8
  - 8: off 12 type u8
  - 9: off 13 type u16+u8

### selector 0 / 一覧・基本表示系
- schema ROM = `0x406D6`
- base = `C4:5CF9`
- record size = `32`
- fields 0..24 が連続定義されている

### selector 3 / キャラ系
- schema ROM = `0x47BF9`
- base = `C4:5863`
- record size = `10`
- fields 0..9 は全部 `u8`

## これで分かった重要な補正
### 1. 道具表・装備表の「本当の base」は schema 基準で見直しが必要
以前の
- 道具表 `0x442BF`
- 装備表 `0x449D0`
は、**「意味のありそうな並びの見え始め」** としては有力だったが、
schema から逆算すると本当の base は

- item base = `0x442AC`
- equip base = `0x449C3`

で、しかも **ID 0 の dummy レコード込み** になっている可能性が高い。

実際、
- item: `0x442AC..0x449C2` は 11バイト刻みでぴったり 165件
- equip: `0x449C3..0x45862` は 16バイト刻みでぴったり 234件

に割り切れる。

## `81:DAC9` の意味の更新
`81:DAC9` は単純な「キャラID→1バイト固定変換」ではなく、実際には:

1. char schema (`C4:7BF9`) から field 0 を読む
2. char schema から field 1 を読む
3. field 1 != 2 なら、field 0 をそのまま後段へ
4. field 1 == 2 のときだけ、現在状態 (`$1398`, `$1929`, `$1986` など) を見て特別計算
5. 最後に `82:B98E` で正規化して返す

という構造。

つまり、**キャラ表示コードは「固定表の直引き」ではなく、char record + 状態依存補正付き**。

## 文字コード・表示系ゴールへの意味
今回の発見で、
- `4F` 命令が何を抜いているか
- 商品/装備/一覧/キャラの record schema
- キャラ表示コード生成が schema 駆動であること

が一気につながった。

まだ未解決なのは
- 最終 glyph / tile 番号への変換
- 会話本文の文字列本体
- 圧縮/辞書の有無と構造

だが、少なくとも **「表示系は場当たり処理ではなく、schema + field extractor + 表示VM で組まれている」** ことはかなり固い。