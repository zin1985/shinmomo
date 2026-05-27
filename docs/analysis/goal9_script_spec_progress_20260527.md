# Goal9 会話・店・イベントスクリプト仕様解析進捗（2026-05-27）

## Goal9の対象

会話・店・イベントスクリプトの仕様書を作ること。
既存引継ぎでは、`31DE0/320A4` の2バイト命令列化、`39850/39993` blob兄弟性、local runner 理解が前進し、58%程度とされていた。

## 今回の追加解析

### 1. `0x41A10` target table 展開

`raw 0x41A10` から 8-byte record を160件展開した。
形式は既存仮説どおり、以下で扱える。

```text
[key][c1][c2][c3][c4][c5][target_lo][target_hi]
```

`target_file_offset = 0x30000 + target_16` として展開し、preview bytes を保存した。

重要anchor:

- record 68: `target=0x39850`
- record 107: `target=0x39993`

### 2. `398xx` 9-byte row series

`0x39800..0x39A80` で `38 05` から始まる 9-byte row を抽出した。
抽出件数: **43 件**。

series counts:

```text
A_F09A:23, B_F0DB:20
```

A系は末尾 `9A F0`、B系は末尾 `DB F0` を持つ。
これは 260510Y 側の `$83:F09A / $83:F0DB` terminal runner 説と整合する。

### 3. script / blob window 保存

以下の候補帯を96 bytes窓として保存した。

```text
0x31C68, 0x31DDF, 0x31DF8, 0x320A4, 0x320C8, 0x39847, 0x39850, 0x39916, 0x39993
```

## 進捗更新

- 旧見立て: 58%
- 今回更新: **62〜64%**

## 残課題

1. `0x41A10` reader 本体はまだ未発見。
2. `398xx/399xx` row が命令なのか、runner用 compact data なのかを runtime で判定する。
3. `0x31C68/0x31DDF/0x320A4/0x320C8` を opcode/data/text reference に分割する。
4. Goal3 の WRAM 作業領域と `0x30000` 台 script の書込先を join する。
