# Goal7 武器特殊能力解析進捗（2026-05-27）

## Goal7の対象

武器・装備の特殊能力サブシステムを整理する。
既存引継ぎでは、武器特殊は弱点領域として残っていたが、`CB:01F9 / raw 0x0B01F9` が equipment-id based script-pack pointer table である見立てが出ていた。

## 今回の追加解析

`raw 0x0B01F9` を 16-bit pointer table として読み直した。
この table は **entry 0 が dummy/default** で、装備ID `N` は table entry `N` を使う形が自然。

default pack は以下。

```text
84->03DB 83->03E1 82->0408
```

全230装備を展開した結果、default と異なる pack は **30 件**。
この30件を `data/static/goal7_weapon_script_pack_by_equipment_20260527.csv` に保存した。

代表的な non-default 装備:

```text
16:玄武の刀、17:白虎の刀、18:朱雀の刀、19:青龍の刀、20:酒呑の剣、60:夕凪のモリ、61:朝凪のモリ、114:出刃包丁、115:小出刃包丁、116:薄切り包丁、117:牛切り包丁、118:葉切り包丁、119:合出刃包丁、120:柳刃包丁、121:骨切り包丁、122:切り出し包丁、123:ドス、124:長ドス
```

hook出現数:

```text
0x84:230, 0x83:230, 0x82:230, 0xC8:19, 0xC1:6, 0xC2:2
```

特殊hook出現数:

```text
0xC8:19, 0xC1:6, 0xC2:2
```

## 今回強くなったこと

- `0x0B01F9` は装備ID別 script-pack pointer table として扱える。
- `84/83/82` はdefault packの基本hook。
- `C1/C2/C8` が追加される装備、または `83/84` target が差し替わる装備が特殊処理候補。
- 玄武・白虎・朱雀・青龍・酒呑、浦島モリ系、包丁/ドス/村雨/村正/孫六/菊一文字、錫杖系、鬼のかぎづめが non-default 側にまとまる。

## 進捗更新

- 旧見立て: 45〜50%相当
- 今回更新: **60〜62%**

## 残課題

1. `C1/C2/C8` の hook class 意味を battle routine 側へ接続する。
2. `data/static/goal7_hook_body_windows_20260527.csv` の body bytes から、damage/status/stat/回復/消費などの効果カテゴリを割る。
3. `83` hook target の差し替えが、表示文・命中判定・対象条件のどれかを判定する。
4. 30件の non-default 装備を効果カテゴリ付きCSVへ拡張する。
