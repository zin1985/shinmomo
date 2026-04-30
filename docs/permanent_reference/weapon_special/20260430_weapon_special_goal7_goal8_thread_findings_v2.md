# Goal 7 / Goal 8 作業仮説整理 v2（2026-04-30）

## 検算済みアンカー

`data/rom_anchor_checks/20260430_weapon_special_anchor_bytes.csv` に保存。

重要アンカー:

- `0x0B01F9`: 2-byte pointer table 候補。
- `0x0B03D1`: `84 db 03 83 e1 03 82 08 04` を含む top-level script header 候補。
- `0x0B03E1`: default op83 body 候補。
- `0x0B0408`: fallback / op82 default body 候補。
- `0x0AD800` / `0x0BD800`: dispatch table 候補として過去ターンで挙げたが、現時点では未確定の比較用アンカー。

## 強い仮説

```text
0x0B01F9..
  = 装備ID別 2-byte pointer table 候補

CB:03D1..
  = weapon special top-level script body 候補

84 / 83 / 82 / C1 / C2 / C8
  = top-level hook command 候補

83
  = weapon effect selector 決定系 hook 候補

A4 xx
  = selector 一時設定候補

C0
  = selector commit / finalize / dispatch trigger 候補

B5
  = script return / end 候補

B2
  = 条件分岐候補
```

## 保留・未確定

- `A4` handler の実アドレス。
- `C0` handler の実アドレス。
- `B2` handler の実アドレス。
- `selector` の bit構造。
- `CA:D800..CA:DF00` が dispatch table かどうか。
- `7E:3000台` が VMStatusSlots かどうか。
- C1/C2/C8 の厳密タイミング。
- selector -> battle effect の完全対応。

## 次の検証コマンド案

ROMが手元にある環境で以下を実行する。

```bash
python scripts/analysis/extract_weapon_special_anchor_bytes.py "Shin Momotarou Densetsu (J).smc"
```

その後、以下を grep / binary search。

```text
84 DB 03 83 E1 03 82 08 04
A4 ?? C0 B5
B2 ??
A0 E1 03 CB
```

## v2での扱い

このファイルは `permanent_reference` 配下だが、内容は「永久保存すべき作業仮説」の位置づけ。確定済み仕様書ではない。
